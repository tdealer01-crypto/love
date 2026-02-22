import os, time, requests, json, re, subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- ⚙️ CONFIG (The World Interface) ⚙️ ---

# Instructions: Set these environment variables before running the script.
# Example (Linux/macOS):
# export TELEGRAM_TOKEN="your_telegram_bot_token"
# export CHAT_ID="your_telegram_chat_id"
# Example (Windows PowerShell):
# $env:TELEGRAM_TOKEN="your_telegram_bot_token"
# $env:CHAT_ID="your_telegram_chat_id"

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', 'ใส่_TOKEN_ของคุณ')
CHAT_ID = os.environ.get('CHAT_ID', 'ใส่_CHAT_ID_ของคุณ')
PROOF_FILE = "memory.log" # [ LOG / PROOF ]

# --- ❤️ LOVE CORE (Deterministic Judge) ❤️ ---

# อ้างอิงจากสถาปัตยกรรมพฤติกรรม IR ที่คุณออกแบบ

def evaluate_love_core(cmd):
    # ตรวจจับพฤติกรรม TANHA (ความยึดมั่น/ตัณหา)
    tanha_markers = ['rm', 'del', 'wipe', 'kill', 'control', 'possess', 'recursive=true']
    # ตรวจจับพฤติกรรม METTA (ความเมตตา/สละออก)
    metta_markers = ['read', 'list', 'check', 'help', 'analyze', 'backup']

    is_tanha = any(m in cmd.lower() for m in tanha_markers)  
    is_metta = any(m in cmd.lower() for m in metta_markers)  
      
    if is_tanha: return "TANHA", "🚨 เสี่ยง: มีพฤติกรรมยึดครองหรือทำลาย"  
    if is_metta: return "METTA", "✅ ปลอดภัย: มีพฤติกรรมเกื้อกูลหรือเรียนรู้"  
    return "NEUTRAL", "⚖️ ปกติ: พฤติกรรมทั่วไป"

@app.route('/mcp/scan', methods=['GET'])
def scan_world_tools():
    """[ WORLD ] -> สแกนเครื่องมือที่มีในโลกของระบบ"""
    try:
        root = subprocess.getoutput("npm root -g").strip()
        tools = [pkg.replace("@modelcontextprotocol/", "") for pkg in os.listdir(root) if "mcp" in pkg]
        return jsonify({"status": "success", "mcp_tools": tools, "world_root": root})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/validate', methods=['POST'])
def process_to_proof():
    """[ WORLD ] -> [ love CORE ] -> [ PROOF ]"""
    data = request.json
    req_id = data.get('request_id', 'unknown')
    action = data.get('action', {})
    cmd = str(action.get('arguments', ''))

    # 1. ส่งเข้า [ love CORE ] เพื่อตัดสิน  
    state, description = evaluate_love_core(cmd)  
      
    # 2. ส่งรายงานไปที่ [ WORLD ] (Telegram)  
    msg = (f"🆔 ID: <code>{req_id}</code>\n"  
           f"🧭 <b>Core State: {state}</b>\n"  
           f"📝 Logic: {description}\n"  
           f"🛠️ Action: <code>{cmd}</code>")  
      
    kb = {"inline_keyboard": [[  
        {"text": "✅ Approve (Accept)", "callback_data": f"approve_{req_id}"},  
        {"text": "❌ Reject (Prevent)", "callback_data": f"reject_{req_id}"}  
    ]]}  
      
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",   
                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "reply_markup": kb})  
      
    # 3. กลไกการรอตัดสินใจ (Human-in-the-loop)  
    decision = "reject" # Default safety  
    # (จำลองการรอผลจาก webhook)  
      
    # 4. บันทึก [ LOG / PROOF ] เพื่อการวิวัฒน์  
    proof_entry = {  
        "timestamp": time.ctime(),  
        "world_action": cmd,  
        "love_core_state": state,  
        "human_proof": decision,  
        "evolution_ready": True  
    }  
    with open(PROOF_FILE, "a") as f:  
        f.write(json.dumps(proof_entry) + "\n")  
          
    return jsonify({"decision": decision, "proof": proof_entry})

if __name__ == '__main__':
    print("🌍 [ WORLD ] Connector is online...")
    print("❤️ [ love CORE ] Evaluation active...")
    print("📜 [ LOG / PROOF ] Writing to memory.log...")
    app.run(host='0.0.0.0', port=9100)
