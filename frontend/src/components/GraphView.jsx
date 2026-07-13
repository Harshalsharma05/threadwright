import { useState, useEffect } from 'react';
import axios from 'axios';
import NodeBox from './NodeBox';

export default function GraphView({ statuses, runId }) {

    // New state to hold the rich data (like sources) from the REST API
    const [nodeData, setNodeData] = useState({});

    // Fetch the full metadata whenever the socket reports a status change
    useEffect(() => {
        if (runId) {
            axios.get(`${import.meta.env.VITE_API_BASE_URL}/runs/${runId}`)
                .then(res => setNodeData(res.data.nodes || {}))
                .catch(err => console.error("Failed to fetch rich node data", err));
        } else {
            setNodeData({});
        }
    }, [runId, statuses]);

    // 1. Defining the SVGs (Standard 24x24 icons)
    const icons = {
        // Newspaper/Globe search for Tavily
        news: <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" /></svg>,
        // GitHub Brand Logo
        github: <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>,
        // Reddit Brand Logo
        reddit: (
            <svg 
                className="w-10 h-10" 
                viewBox="0 0 32 32" 
                fill="none" 
                xmlns="http://www.w3.org/2000/svg"
            >
                <path 
                    fillRule="evenodd" 
                    clipRule="evenodd" 
                    d="M20.0193 8.90951C20.0066 8.98984 20 9.07226 20 9.15626C20 10.0043 20.6716 10.6918 21.5 10.6918C22.3284 10.6918 23 10.0043 23 9.15626C23 8.30819 22.3284 7.6207 21.5 7.6207C21.1309 7.6207 20.7929 7.7572 20.5315 7.98359L16.6362 7L15.2283 12.7651C13.3554 12.8913 11.671 13.4719 10.4003 14.3485C10.0395 13.9863 9.54524 13.7629 9 13.7629C7.89543 13.7629 7 14.6796 7 15.8103C7 16.5973 7.43366 17.2805 8.06967 17.6232C8.02372 17.8674 8 18.1166 8 18.3696C8 21.4792 11.5817 24 16 24C20.4183 24 24 21.4792 24 18.3696C24 18.1166 23.9763 17.8674 23.9303 17.6232C24.5663 17.2805 25 16.5973 25 15.8103C25 14.6796 24.1046 13.7629 23 13.7629C22.4548 13.7629 21.9605 13.9863 21.5997 14.3485C20.2153 13.3935 18.3399 12.7897 16.2647 12.7423L17.3638 8.24143L20.0193 8.90951ZM12.5 18.8815C13.3284 18.8815 14 18.194 14 17.3459C14 16.4978 13.3284 15.8103 12.5 15.8103C11.6716 15.8103 11 16.4978 11 17.3459C11 18.194 11.6716 18.8815 12.5 18.8815ZM19.5 18.8815C20.3284 18.8815 21 18.194 21 17.3459C21 16.4978 20.3284 15.8103 19.5 15.8103C18.6716 15.8103 18 16.4978 18 17.3459C18 18.194 18.6716 18.8815 19.5 18.8815ZM12.7773 20.503C12.5476 20.3462 12.2372 20.4097 12.084 20.6449C11.9308 20.8802 11.9929 21.198 12.2226 21.3548C13.3107 22.0973 14.6554 22.4686 16 22.4686C17.3446 22.4686 18.6893 22.0973 19.7773 21.3548C20.0071 21.198 20.0692 20.8802 19.916 20.6449C19.7628 20.4097 19.4524 20.3462 19.2226 20.503C18.3025 21.1309 17.1513 21.4449 16 21.4449C15.3173 21.4449 14.6345 21.3345 14 21.1137C13.5646 20.9621 13.1518 20.7585 12.7773 20.503Z" 
                    fill="currentColor" 
                />
            </svg>
        ),
        // Document with code for Parsing
        parse: <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>,
        // Sparkles for Synthesis
        synthesize: <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>
    };

    const nodes = {
        search_news: { id: 'search_news', label: 'News Search', icon: icons.news, delay: '0ms' },
        github_signal: { id: 'github_signal', label: 'GitHub Signal', icon: icons.github, delay: '200ms' },
        reddit_signal: { id: 'reddit_signal', label: 'Reddit Signal', icon: icons.reddit, delay: '400ms' },
        parse_job: { id: 'parse_job', label: 'Parse Job Postings', icon: icons.parse, delay: '600ms' },
        synthesize: { id: 'synthesize', label: 'Synthesize Brief', icon: icons.synthesize, delay: '0ms' }
    };

    const topRowDone = 
        statuses.search_news === 'done' && 
        statuses.github_signal === 'done' && 
        statuses.reddit_signal === 'done' && 
        statuses.parse_job === 'done';

    const paths = [
        "M125,0 C125,60 500,60 500,120",
        "M375,0 C375,60 500,60 500,120",
        "M625,0 C625,60 500,60 500,120",
        "M875,0 C875,60 500,60 500,120"
    ];

    return (
        <div className="p-8 bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-xl overflow-hidden shadow-2xl mt-8 flex flex-col items-center">
            
            {/* Added node-float keyframe and animate-float class */}
            <style>{`
                @keyframes dash-gather {
                    to { stroke-dashoffset: -20; }
                }
                @keyframes data-flow {
                    0% { stroke-dashoffset: 1000; }
                    100% { stroke-dashoffset: 0; }
                }
                @keyframes node-float {
                    0%, 100% { transform: translateY(0px); }
                    50% { transform: translateY(-5px); }
                }
                .path-gathering {
                    stroke-dasharray: 6 6;
                    animation: dash-gather 2s linear infinite;
                }
                .path-flow-glow {
                    stroke-dasharray: 60 1000; 
                    animation: data-flow 3s cubic-bezier(0.4, 0, 0.2, 1) infinite;
                    stroke-linecap: round;
                }
                .animate-float {
                    animation: node-float 3s ease-in-out infinite;
                }
            `}</style>

            <div className="w-full max-w-4xl relative">
                
                {/* Row 1: Parallel Workers */}
                <div className="flex justify-between w-full relative z-50">
                    {/* We map status from 'statuses' (WebSocket), but result from 'nodeData' (REST API) */}
                    <NodeBox {...nodes.search_news} status={statuses[nodes.search_news.id]} result={nodeData[nodes.search_news.id]?.result} />
                    <NodeBox {...nodes.github_signal} status={statuses[nodes.github_signal.id]} result={nodeData[nodes.github_signal.id]?.result} />
                    <NodeBox {...nodes.reddit_signal} status={statuses[nodes.reddit_signal.id]} result={nodeData[nodes.reddit_signal.id]?.result} />
                    <NodeBox {...nodes.parse_job} status={statuses[nodes.parse_job.id]} result={nodeData[nodes.parse_job.id]?.result} />
                </div>

                {/* SVG Connections Area */}
                <div className="w-full h-[120px] -my-2 relative z-0">
                    <svg viewBox="0 0 1000 120" preserveAspectRatio="none" className="w-full h-full overflow-visible">
                        {paths.map((d, i) => (
                            <g key={i}>
                                <path 
                                    d={d}
                                    fill="none" 
                                    stroke={topRowDone ? "#059669" : "#334155"}
                                    strokeWidth={topRowDone ? "3" : "2"}
                                    className={!topRowDone ? "path-gathering" : "transition-colors duration-500"}
                                />
                                {topRowDone && (
                                    <path 
                                        d={d}
                                        fill="none" 
                                        stroke="#34d399"
                                        strokeWidth="4"
                                        className="path-flow-glow drop-shadow-[0_0_8px_rgba(52,211,153,0.8)]"
                                    />
                                )}
                            </g>
                        ))}
                    </svg>
                </div>

                {/* Row 2: Synthesis Handoff */}
                <div className="flex justify-center w-full relative z-10">
                    <NodeBox {...nodes.synthesize} status={statuses[nodes.synthesize.id]} result={nodeData[nodes.synthesize.id]?.result} />
                </div>

            </div>
        </div>
    );
}