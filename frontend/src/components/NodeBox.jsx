import React, { useState } from 'react';

export default function NodeBox({ label, status, icon, delay = "0ms", result }) {

    const [showSources, setShowSources] = useState(false); // Added hover state
    const sources = result?.sources || [];  // Safely extract sources
    const hasSources = sources.length > 0;

    const statusConfig = {
        pending: {
            container: 'bg-slate-900/40 border-slate-700/50 text-slate-500',
            indicator: 'bg-slate-600',
            icon: 'text-slate-600'
        },
        running: {
            container: 'bg-slate-800/80 border-emerald-500/50 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.15)] transform -translate-y-1',
            indicator: 'bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]',
            icon: 'text-emerald-500 drop-shadow-[0_0_8px_rgba(16,185,129,0.8)]' // Added glow to the SVG
        },
        done: {
            container: 'bg-slate-900/80 border-emerald-600 text-slate-200',
            indicator: 'bg-emerald-500 shadow-[0_0_5px_rgba(16,185,129,0.5)]',
            icon: 'text-emerald-500'
        },
        failed: {
            container: 'bg-red-950/20 border-red-500/50 text-red-400',
            indicator: 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]',
            icon: 'text-red-500'
        }
    };

    const currentStyle = statusConfig[status || 'pending'];

    return (
        <div className={`p-4 w-48 border rounded-xl backdrop-blur-sm transition-all duration-300 flex flex-col ${currentStyle.container} ${showSources ? 'z-[9999]' : 'z-10'}`}>
            {/* Header / Status */}
            <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[10px] uppercase tracking-wider opacity-80">
                    {status || 'pending'}
                </span>
                <div className={`w-2.5 h-2.5 rounded-full ${currentStyle.indicator}`}></div>
            </div>
            
            {/* Main Content Area (Floating Icon + Label) */}
            <div className="flex flex-col items-center justify-center my-4 min-h-[60px]">
                {icon && (
                    <div 
                        className={`mb-3 animate-float transition-colors duration-300 ${currentStyle.icon}`}
                        style={{ animationDelay: delay }} // Staggers the floating effect
                    >
                        {icon}
                    </div>
                )}
                <div className="font-bold text-sm tracking-wide leading-tight text-center">
                    {label}
                </div>
            </div>

            {/* Sources Button (Footer) */}
            <div 
                className={`mt-auto pt-3 border-t border-slate-700/50 flex justify-center transition-opacity relative ${status === 'pending' || !hasSources ? 'opacity-30' : 'opacity-100'}`}
                onMouseEnter={() => hasSources && setShowSources(true)}
                onMouseLeave={() => setShowSources(false)}
            >
                <button className="flex items-center gap-1.5 text-[10px] uppercase font-bold text-slate-500 hover:text-cyan-400 transition-colors group">
                    <svg className={`w-3.5 h-3.5 ${currentStyle.icon} group-hover:text-cyan-400 transition-colors`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                    Sources {hasSources && `(${sources.length})`}
                </button>

                {/* THE POPUP: Apple Glass style, pointer arrow, maximum z-index, and fixed hover bridge */}
                {showSources && hasSources && (
                    <div className="absolute top-[100%] left-1/2 -translate-x-1/2 pt-5 -mt-2 w-64">
                        <div className="relative bg-slate-900/80 backdrop-blur-3xl saturate-200 border border-slate-700/80 rounded-xl shadow-[0_8px_32px_rgba(0,0,0,0.6)] p-3 font-mono text-[11px] text-left animate-[dropFade_0.15s_ease-out_forwards]">
                            
                            {/* Upward pointing triangle (Tooltip Arrow) */}
                            <div className="absolute -top-[7px] left-1/2 -translate-x-1/2 w-3.5 h-3.5 bg-slate-800/80 backdrop-blur-xl border-t border-l border-slate-700/50 rotate-45 rounded-tl-sm"></div>
                            
                            {/* Content Wrapper (z-10 keeps it above the arrow) */}
                            <div className="relative z-10 text-slate-400 border-b border-slate-700/50 pb-1.5 mb-2 font-bold flex justify-between items-center">
                                <span># TELEMETRY_LINKS</span>
                                <span className="text-[9px] text-cyan-400/80 tracking-widest">SECURE</span>
                            </div>
                            
                            <ul className="relative z-10 space-y-1 max-h-48 overflow-y-auto pr-1">
                                {sources.map((src, idx) => (
                                    <li key={idx}>
                                        {/* Group specifically named "link" to avoid triggering on outer box hover */}
                                        <a 
                                            href={src.url} 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            className="group/link flex items-center gap-2 text-slate-300 hover:text-cyan-300 hover:bg-slate-800/60 p-1.5 rounded-lg transition-all"
                                            title={src.title} 
                                        >
                                            <span className="text-emerald-500/80 shrink-0 font-bold">[{idx + 1}]</span>
                                            
                                            <span className="truncate flex-1">
                                                {src.title}
                                            </span>
                                            
                                            {/* External Link Icon triggered by group/link */}
                                            <svg className="w-3.5 h-3.5 shrink-0 opacity-0 group-hover/link:opacity-100 transition-opacity text-cyan-400 drop-shadow-[0_0_5px_rgba(34,211,238,0.6)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                            </svg>
                                        </a>
                                    </li>
                                ))}
                            </ul>

                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}