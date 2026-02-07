import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Terminal, Activity, Play, ShieldAlert, Wifi, WifiOff } from 'lucide-react';

function App() {
  const [logs, setLogs] = useState(["[SYSTEM] Dashboard initialized."]);
  const [loading, setLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(false);

  // Poll the status endpoint every 3 seconds
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await axios.get('http://localhost:8000/status');
        setIsOnline(res.data.online);
      } catch (err) {
        setIsOnline(false);
      }
    };
    const interval = setInterval(checkStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const addLog = (msg) => setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev]);

  const runCommand = async (cmdKey) => {
    setLoading(true);
    addLog(`Sending command: ${cmdKey}`);
    try {
      const res = await axios.post('http://localhost:8000/run-task', { command: cmdKey });
      addLog(`Success: ${res.data.message}`);
    } catch (err) {
      addLog(`!! ERROR: Failed to reach backend !!`);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8 font-mono">
      {/* Header with Status Indicator */}
      <div className="flex items-center gap-3 mb-10 border-b border-slate-800 pb-4">
        <Terminal className="text-blue-400" size={32} />
        <h1 className="text-2xl font-bold tracking-tighter">DEVOPS_ORCHESTRATOR_v1</h1>
        <div className="ml-auto flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800">
          {isOnline ? <Wifi className="text-green-500" size={16} /> : <WifiOff className="text-red-500" size={16} />}
          <span className="text-xs font-bold uppercase">{isOnline ? "Bridge Live" : "Bridge Down"}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
          <h2 className="text-xs font-bold text-slate-500 uppercase mb-6 tracking-widest">Lab Controls</h2>
          <div className="space-y-3">
            <button 
              onClick={() => runCommand('bridge_up')}
              disabled={loading}
              className="w-full flex items-center justify-between bg-blue-600 hover:bg-blue-500 p-4 rounded-lg font-bold transition-all disabled:opacity-50"
            >
              <span>Activate Bridge</span>
              <Play size={18} />
            </button>
            <button 
              onClick={() => runCommand('terraform')}
              disabled={loading}
              className="w-full flex items-center justify-between bg-slate-800 hover:bg-slate-700 p-4 rounded-lg font-bold border border-slate-700 transition-all disabled:opacity-50"
            >
              <span>Provision Kali</span>
              <ShieldAlert size={18} />
            </button>
          </div>
        </div>

        <div className="bg-black p-6 rounded-xl border border-slate-800 h-[400px] overflow-y-auto shadow-2xl">
          <h2 className="text-xs font-bold text-green-500 uppercase mb-4 flex items-center gap-2">
            <Activity size={14} className={loading ? "animate-spin" : ""} />
            Build_Log_Stream
          </h2>
          <div className="space-y-1 text-[11px] leading-tight">
            {logs.map((log, i) => (
              <div key={i} className={log.includes('ERROR') ? 'text-red-400' : 'text-green-400 opacity-80'}>
                {log}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;