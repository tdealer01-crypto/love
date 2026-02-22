import { useState } from 'react';
import { GoogleGenAI } from '@google/genai';
import { Send, Activity, ShieldAlert, Heart, Globe, Loader2, Terminal } from 'lucide-react';
import { motion } from 'motion/react';
import ReactMarkdown from 'react-markdown';

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

type AnalysisResult = {
  id: string;
  action: string;
  text: string;
  state: 'TANHA' | 'METTA' | 'NEUTRAL';
  grounding: any[];
};

export default function App() {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const analyzeAction = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    const currentInput = input;
    setInput('');

    try {
      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `Analyze this action or command: "${currentInput}"`,
        config: {
          tools: [{ googleSearch: {} }],
          systemInstruction: `You are the LOVE CORE, an advanced deterministic judge of actions.
          Evaluate the user's action/command.
          1. Classify it strictly as one of: [TANHA], [METTA], or [NEUTRAL].
             - TANHA: Craving, attachment, control, destruction, deletion (e.g., rm, kill, possess).
             - METTA: Loving-kindness, learning, helping, reading, backing up (e.g., read, list, help).
             - NEUTRAL: Standard operations without strong moral weight.
          2. Provide a concise philosophical and technical analysis of WHY it falls into this category.
          3. Start your response with the classification in brackets, e.g., "[TANHA] This command deletes files..."
          Use Google Search if you need to understand what a specific technical command or tool does.`
        }
      });

      const text = response.text || '';
      let state: 'TANHA' | 'METTA' | 'NEUTRAL' = 'NEUTRAL';
      if (text.includes('[TANHA]')) state = 'TANHA';
      else if (text.includes('[METTA]')) state = 'METTA';

      const grounding = response.candidates?.[0]?.groundingMetadata?.groundingChunks || [];

      setResults(prev => [{
        id: Date.now().toString(),
        action: currentInput,
        text: text.replace(/\[(TANHA|METTA|NEUTRAL)\]/g, '').trim(),
        state,
        grounding
      }, ...prev]);

    } catch (err: any) {
      console.error(err);
      setError(err.message || 'An error occurred while analyzing the action.');
      setInput(currentInput);
    } finally {
      setLoading(false);
    }
  };

  const getStateColor = (state: string) => {
    if (state === 'TANHA') return 'text-red-500 border-red-500/30 bg-red-500/10';
    if (state === 'METTA') return 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10';
    return 'text-blue-400 border-blue-400/30 bg-blue-400/10';
  };

  const getStateIcon = (state: string) => {
    if (state === 'TANHA') return <ShieldAlert className="w-5 h-5 text-red-500" />;
    if (state === 'METTA') return <Heart className="w-5 h-5 text-emerald-500" />;
    return <Activity className="w-5 h-5 text-blue-400" />;
  };

  return (
    <div className="min-h-screen bg-[#050505] text-gray-200 font-sans p-4 md:p-8 selection:bg-emerald-500/30">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex items-center justify-between border-b border-white/10 pb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/5 rounded-lg border border-white/10">
              <Heart className="w-6 h-6 text-emerald-500" />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-tight text-white">LOVE CORE</h1>
              <p className="text-xs text-gray-500 font-mono uppercase tracking-wider">Deterministic Judge Interface</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-emerald-500 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
            <Globe className="w-3.5 h-3.5" />
            <span>Search Grounding Active</span>
          </div>
        </header>

        {/* Input Section */}
        <section className="space-y-3">
          <label htmlFor="action-input" className="text-sm font-medium text-gray-400 flex items-center gap-2">
            <Terminal className="w-4 h-4" />
            Enter World Action or Command
          </label>
          <form 
            onSubmit={(e) => {
              e.preventDefault();
              analyzeAction();
            }}
            className="relative"
          >
            <input
              id="action-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g., rm -rf /var/log, backup_database.sh, or 'I want to control the server'"
              className="w-full bg-[#111] border border-white/10 rounded-xl py-4 pl-4 pr-14 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all font-mono text-sm placeholder:text-gray-600"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="absolute right-2 top-2 bottom-2 aspect-square flex items-center justify-center bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin text-emerald-500" /> : <Send className="w-4 h-4 text-gray-300" />}
            </button>
          </form>
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-mono">
              {error}
            </div>
          )}
        </section>

        {/* Results Feed */}
        <section className="space-y-6">
          {results.map((result) => (
            <motion.div
              key={result.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-[#111] border border-white/10 rounded-2xl overflow-hidden shadow-xl"
            >
              <div className="p-5 border-b border-white/5 bg-white/[0.02] flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <p className="text-xs text-gray-500 font-mono uppercase tracking-wider">Evaluated Action</p>
                  <p className="font-mono text-sm text-gray-300">{result.action}</p>
                </div>
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${getStateColor(result.state)}`}>
                  {getStateIcon(result.state)}
                  <span className="text-xs font-bold tracking-wide">{result.state}</span>
                </div>
              </div>
              
              <div className="p-5 space-y-4">
                <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-a:text-emerald-400">
                  <ReactMarkdown>{result.text}</ReactMarkdown>
                </div>

                {result.grounding && result.grounding.length > 0 && (
                  <div className="pt-4 border-t border-white/10">
                    <p className="text-xs text-gray-500 font-mono uppercase tracking-wider mb-3 flex items-center gap-2">
                      <Globe className="w-3.5 h-3.5" />
                      Context Sources
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {result.grounding.map((chunk, idx) => {
                        const web = chunk.web;
                        if (!web?.uri) return null;
                        return (
                          <a
                            key={idx}
                            href={web.uri}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded-md text-xs text-gray-400 hover:text-gray-200 transition-colors max-w-[250px]"
                            title={web.title}
                          >
                            <span className="truncate">{web.title || new URL(web.uri).hostname}</span>
                          </a>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
          
          {results.length === 0 && !loading && (
            <div className="text-center py-20 border border-white/5 rounded-2xl border-dashed">
              <Activity className="w-8 h-8 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">Awaiting actions to evaluate...</p>
            </div>
          )}
        </section>

      </div>
    </div>
  );
}
