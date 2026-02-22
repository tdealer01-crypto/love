import os, time, requests, json, re, subprocess, threading, logging
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==========================================================
# ⚙️ CONFIG & LOGGING
# ==========================================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', 'ใส่_TOKEN_ของคุณ')
CHAT_ID = os.environ.get('CHAT_ID', 'ใส่_CHAT_ID_ของคุณ')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
LOG_FILE = "agent_audit.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ==========================================================
# 🧠 LLM & LOVE CORE (Policy Engine Layer)
# ==========================================================
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        gemini_model.generate_content("Test", request_options={"timeout": 10})
        print("✅ [ Gemini ] API Key is valid and Model loaded successfully.")
        logging.info("Gemini model loaded successfully.")
    except Exception as e:
        print(f"❌ [ Gemini ] API Key is INVALID or failed to connect: {e}")
        logging.error(f"Gemini connection failed: {e}")
        gemini_model = None
else:
    gemini_model = None
    print("⚠️ [ Gemini ] API Key not found. LLM features will be disabled.")
    logging.warning("Gemini API Key not found.")

BLOCKED_COMMANDS = ["rm -rf", "shutdown", "reboot", ":(){:|:&};:"]
SENSITIVE_PATHS = ["/etc/", "/root/", "/var/log/"]

def evaluate_policy(shell_command):
    """
    Evaluates a shell command against a set of security rules.
    - Blocks explicitly forbidden command patterns.
    - Prevents modification of sensitive system directories.
    - Allows file creation/modification in non-sensitive areas.
    """
    
    # Rule 1: Block highly destructive, hardcoded command patterns
    for blocked in BLOCKED_COMMANDS:
        if blocked in shell_command:
            logging.warning(f"Policy REJECT (Dangerous Pattern): {shell_command}")
            return "reject", f"Blocked dangerous command pattern: `{blocked}`"

    # Rule 2: Prevent operations in sensitive directories
    modifies_fs = any(cmd in shell_command for cmd in ['>', '>>', 'mv', 'cp', 'mkdir', 'touch', 'chmod', 'chown', 'rm'])
    if modifies_fs:
        for path in SENSITIVE_PATHS:
            # Check if the command operates on a sensitive path
            if re.search(rf'(\s|"){re.escape(path)}', shell_command):
                 logging.warning(f"Policy REJECT (Sensitive Path): {shell_command}")
                 return "reject", f"Blocked attempt to modify sensitive path: `{path}`"

    # Rule 3: Specific constraints on `rm`
    if ' rm ' in f' {shell_command} ' and ('-r' in shell_command or '-f' in shell_command or '/*' in shell_command):
        logging.warning(f"Policy REJECT (Recursive/Forced RM): {shell_command}")
        return "reject", "Blocked recursive or forced `rm`. Only single file deletion is allowed."

    # If no rules are broken, approve the command.
    logging.info(f"Policy APPROVE: {shell_command}")
    return "approve", "Command approved by policy engine."

MEMORY_FILE = "agent_memory.md"

def get_memory_context():
    """Reads the content of the memory file to provide context to the LLM."""
    try:
        with open(MEMORY_FILE, "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Memory file not found. Proceeding with no context."
    except Exception as e:
        return f"Error reading memory file: {e}"

def translate_to_shell_with_gemini(natural_command):
    if not gemini_model:
        return 'echo "Gemini is not available. Please check your API Key."', "LLM Disabled"
    
    memory_context = get_memory_context()

    prompt = f"""# CONTEXT
## Main Objective & Memory
{memory_context}

# TASK
As a senior Linux system administrator AI, translate the user's request into a single, executable, and safe shell command for a Termux environment.

# RULES
- **CRITICAL:** Do NOT use `sudo`.
- The output MUST be a single-line shell command.
- If the request is unsafe, ambiguous, or cannot be translated, return the single word: 'ERROR'.

# REQUEST
User: "{natural_command}"
Command:"""
    try:
        response = gemini_model.generate_content(prompt)
        # Clean up the response, removing backticks and "Command:" prefixes
        shell_command = response.text.strip().replace('`', '')
        if shell_command.lower().startswith("command:"):
            shell_command = shell_command[8:].strip()

        if not shell_command or 'ERROR' in shell_command.upper():
             logging.warning(f"Gemini returned an error or ambiguous command for: '{natural_command}'")
             return f'echo "Error: Gemini deemed the request ambiguous or unsafe."', "LLM Error"
        return shell_command, "LLM Translation"
    except Exception as e:
        logging.error(f"Gemini API call failed: {e}")
        return f'echo "Error: Could not contact Gemini API. {e}"', "LLM Error"

# ==========================================================
# 📡 TELEGRAM AGENT (User Interface Layer)
# ==========================================================
last_update_id = 0
last_command_time = 0
COMMAND_COOLDOWN = 5 # 5 seconds

def send_telegram_message(chat_id, text):
    # ... (This function remains the same)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try: requests.post(url, json=payload)
    except Exception as e: print(f"Error sending to Telegram: {e}")

def handle_telegram_updates():
    global last_update_id, last_command_time
    print("🤖 [ Agent ] Listening for commands from Telegram...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=60"
            response = requests.get(url, timeout=70).json()
            for update in response.get('result', []):
                last_update_id = update['update_id']
                message = update.get('message')
                if message and 'text' in message:
                    chat_id = message['chat']['id']
                    current_time = time.time()
                    if current_time - last_command_time < COMMAND_COOLDOWN:
                        send_telegram_message(chat_id, "⏳ Cooldown active. Please wait a moment.")
                        continue
                    last_command_time = current_time

                    natural_command = message['text'].strip()
                    logging.info(f"Received command from chat_id {chat_id}: {natural_command}")

                    # 1. Translate with LLM
                    shell_command, source = translate_to_shell_with_gemini(natural_command)
                    logging.info(f"Gemini translated '{natural_command}' to '{shell_command}'")

                    # 2. Validate with Policy Engine (LOVE CORE)
                    decision, hint = evaluate_policy(shell_command)
                    logging.info(f"Policy engine decision for '{shell_command}': {decision} - {hint}")

                    # 3. Execute or Reject
                    output = ""
                    if decision == "approve":
                        try: output = subprocess.getoutput(shell_command)
                        except Exception as e: output = f"Execution Error: {e}"
                    else:
                        output = f"COMMAND REJECTED BY LOVE CORE:\n{hint}"

                    response_text = (
                        f"💬 <b>Request:</b> {natural_command}\n"
                        f"🤖 <b>Interpreted as:</b> <code>{shell_command}</code>\n"
                        f"❤️ <b>Policy Decision:</b> {decision.upper()}\n\n"
                        f"<b>--- Execution Result ---</b>\n"
                        f"<pre>{output or '(No output)'}</pre>"
                    )
                    send_telegram_message(chat_id, response_text)
        except Exception as e:
            logging.error(f"Main loop error: {e}")
            time.sleep(10)

# ==========================================================
# 🚀 START SERVER
# ==========================================================
if __name__ == '__main__':
    telegram_thread = threading.Thread(target=handle_telegram_updates, daemon=True)
    telegram_thread.start()
    print("🚀 Agent is online and ready.")
        # Keep main thread alive for the background thread
    while True:
        time.sleep(60)
