import { useState } from 'react';
import axios from 'axios';
import { useWorkflowSocket } from './hooks/useWorkflowSocket';
import GraphView from './components/GraphView';
import DemoControls from './components/DemoControls';
import ResultPanel from './components/ResultPanel';
import { BackgroundRippleEffect } from './components/ui/background-ripple-effect';

function App() {
  const [company, setCompany] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [runId, setRunId] = useState(() => sessionStorage.getItem('currentRunId') || null);
  const [injectFailure, setInjectFailure] = useState(false);
  
  const statuses = useWorkflowSocket(runId);

  const handleRun = async () => {
    if (!company.trim()) return;

    // Clear previous state if running a new one
    setRunId(null);
    sessionStorage.removeItem('currentRunId');
    
    try {
      const res = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/runs`, {
        company_name: company,
        job_description: jobDescription,
        inject_failure: injectFailure // Passed to backend for the retry demo
      });

      const newRunId = res.data.workflow_run_id;

      setRunId(newRunId);
      sessionStorage.setItem('currentRunId', newRunId);
    } catch (err) {
      console.error('Failed to start run. Is the backend running?', err);
    }
  };

return (
<div className="relative flex min-h-screen w-full flex-col bg-slate-950 overflow-x-hidden font-sans select-none">
      
      {/* The background grid sits perfectly at the back */}
      <BackgroundRippleEffect />

      {/* z-10 moves the actionable UI containers cleanly over the grid rows */}
      <div className="relative z-10 p-8 max-w-5xl mx-auto w-full">
        
        <h1 className="text-4xl font-black mb-8 tracking-tight bg-gradient-to-r from-slate-100 to-slate-400 bg-clip-text text-transparent">
          Threadwright
        </h1>
        
        <DemoControls injectFailure={injectFailure} setInjectFailure={setInjectFailure} />

        {/* Translucent backdrop-blur container allows the grids behind to subtly show through */}
        <div className="flex flex-col gap-4 mb-4 bg-slate-900/60 backdrop-blur-md p-6 rounded-xl border border-slate-800 shadow-xl">
          <div className="flex gap-4">
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Enter company name (e.g., Blinkit)..."
              className="bg-slate-950 border border-slate-800 text-slate-200 p-3 rounded-lg flex-1 shadow-inner focus:outline-none focus:ring-2 focus:ring-emerald-500 placeholder-slate-500 font-mono text-sm"
            />
            <button
              onClick={handleRun}
              className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold px-8 py-3 rounded-lg shadow-md transition-all border border-emerald-400/30 active:scale-[0.98]"
            >
              RUN_GRAPH
            </button>
          </div>
          
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Optional: Paste raw Job Description (JD) keywords here to direct deep searches..."
            className="bg-slate-950 border border-slate-800 text-slate-200 p-3 rounded-lg w-full h-32 shadow-inner focus:outline-none focus:ring-2 focus:ring-emerald-500 font-sans text-sm resize-y placeholder-slate-500"
          />
        </div>

        {runId && (
          <div className="mt-8 transition-all">
              <h2 className="text-sm font-mono text-slate-500 mb-4 tracking-widest">
                RUN_TRACE_ID: <span className="text-slate-400">{runId}</span>
              </h2>
              
              <GraphView statuses={statuses} runId={runId} />
              
              <ResultPanel 
                  runId={runId} 
                  synthesizeStatus={statuses['synthesize']}
                  company={company}
              />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;