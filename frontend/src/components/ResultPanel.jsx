import { useState, useEffect, useRef } from "react";
import axios from "axios";

import { TypewriterText } from "./ui/TypewriterText";
import { TerminalSkeleton } from "./ui/TerminalSkeleton";

// --- Terminal Components ---
const TermRow = ({ label, value, delay }) => (
  <div
    className="flex flex-col sm:flex-row sm:gap-4 term-animate"
    style={{ animationDelay: delay }}
  >
    <span className="text-slate-500 w-48 shrink-0">--{label}:</span>
    <span className="text-slate-300">{value}</span>
  </div>
);

const TermArray = ({ label, items, colorClass, delay }) => (
  <div
    className="flex flex-col sm:flex-row sm:gap-4 term-animate"
    style={{ animationDelay: delay }}
  >
    <span className="text-slate-500 w-48 shrink-0">--{label}:</span>
    <div className="flex flex-wrap gap-2">
      {items?.map((item, i) => (
        <span
          key={item}
          className={`px-2 py-0.5 border text-xs bg-opacity-10 opacity-0 animate-[revealWord_0.2s_ease-out_forwards] ${colorClass}`}
          style={{ animationDelay: `calc(${delay} + ${i * 100}ms)` }}
        >
          [{item}]
        </span>
      ))}
    </div>
  </div>
);

export default function ResultPanel({ runId, synthesizeStatus, company }) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const terminalRef = useRef(null); // 1. Ref for auto-scrolling

  // Auto-scroll when results arrive
  useEffect(() => {
    if (result && terminalRef.current) {
      setTimeout(() => {
        terminalRef.current.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 100); // Slight delay ensures DOM is fully painted
    }
  }, [result]);

  useEffect(() => {
    if (synthesizeStatus === "done" && runId) {
      axios
        .get(`${import.meta.env.VITE_API_BASE_URL}/runs/${runId}`)
        .then((res) => {
          const rawResult = res.data.nodes?.synthesize?.result;
          const parsedData =
            typeof rawResult === "string" ? JSON.parse(rawResult) : rawResult;
          setResult(parsedData);
        })
        .catch((err) => {
          console.error("Failed to fetch results", err);
          setError("ERR_CONNECTION_REFUSED");
        });
    } else if (
      synthesizeStatus === "running" ||
      synthesizeStatus === "pending"
    ) {
      // Reset state for new runs
      setResult(null);
      setError(null);
    }
  }, [runId, synthesizeStatus]);

  // Define keywords array here instead
  const keywords = [
    "Scalability",
    "System Design",
    "Cloud",
    "Java",
    "React",
    "Performance",
    "Reliability",
    "Innovation",
  ];

  // If the workflow hasn't even reached the synthesis node yet, don't show the terminal
  // if (!runId || (synthesizeStatus !== 'running' && synthesizeStatus !== 'done' && !error)) return null;

  return (
    <div className="mt-8" ref={terminalRef}>
      <style>{`
                @keyframes typeIn {
                    from { opacity: 0; transform: translateX(-5px); }
                    to { opacity: 1; transform: translateX(0); }
                }
                @keyframes revealWord {
                    from { opacity: 0; filter: blur(2px); }
                    to { opacity: 1; filter: blur(0); }
                }
                .term-animate {
                    opacity: 0;
                    animation: typeIn 0.2s ease-out forwards;
                }
                @keyframes blink {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0; }
                }
                .cursor-blink {
                    display: inline-block;
                    width: 8px;
                    height: 15px;
                    background-color: #34d399;
                    animation: blink 1s step-end infinite;
                    vertical-align: middle;
                    margin-left: 4px;
                }
            `}</style>

      <div className="bg-[#0f172a] rounded-lg border border-slate-700 shadow-2xl overflow-hidden font-mono text-sm min-h-[400px]">
        {/* Terminal Header */}
        <div className="bg-[#1e293b] px-4 py-2 border-b border-slate-700 flex items-center justify-between sticky top-0 z-10">
          <div className="flex gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
          </div>
          <span className="text-slate-500 text-xs">
            threadwright@engine: ~/output
          </span>
        </div>

        <div className="p-6">
          {error ? (
            <div className="text-red-500">
              <span className="font-bold">[FATAL]</span> {error}
            </div>
          ) : !runId ? (
            /* IDLE SKELETON STATE (Dimmed out) */
            <div className="opacity-40 grayscale pointer-events-none transition-all duration-700">
              <div className="text-slate-500 font-bold mb-6">
                $ ./synthesize_intel.sh --status="AWAITING_INPUT"
                <span className="cursor-blink"></span>
              </div>
              <TerminalSkeleton />
            </div>
          ) : !result ? (
            /* RUNNING STATE (Bright green, actively processing) */
            <div className="animate-pulse">
              <div className="text-emerald-500 font-bold mb-6">
                $ ./synthesize_intel.sh --target="{company || "PROCESSING"}"
                <span className="cursor-blink"></span>
              </div>
              <TerminalSkeleton />
            </div>
          ) : (
            /* Actual Data Payload with Animations */
            <div className="space-y-6">
              <div
                className="text-emerald-500 font-bold term-animate"
                style={{ animationDelay: "0ms" }}
              >
                $ ./synthesize_intel.sh --target="{company || "UNKNOWN"}"
                <br />
                <span className="text-slate-400 font-normal">
                  STATUS: 200 OK | PAYLOAD: DECRYPTED
                </span>
              </div>

              <div
                className="border-l-2 border-indigo-500 pl-4 py-2 bg-indigo-950/30 term-animate"
                style={{ animationDelay: "100ms" }}
              >
                <div className="text-indigo-400 mb-2"># STRATEGY_OVERRIDE</div>
                <p className="text-slate-300 leading-relaxed">
                  <TypewriterText
                    text={result.strategic_interview_advice}
                    delayOffset={200}
                    highlightKeywords={keywords}
                  />
                </p>
              </div>

              <div
                className="grid grid-cols-1 md:grid-cols-2 gap-8 border-y border-slate-800 py-4 term-animate"
                style={{ animationDelay: "1500ms" }}
              >
                <div className="space-y-2">
                  <div className="text-slate-500 mb-2"># MARKET_METRICS</div>
                  <TermArray
                    label="COMPETITORS"
                    items={result.market_and_competition?.direct_competitors}
                    colorClass="border-slate-600 text-slate-400"
                    delay="1600ms"
                  />
                  <TermRow
                    label="POSITION"
                    value={
                      <TypewriterText
                        text={
                          result.market_and_competition
                            ?.market_position_and_challenges
                        }
                        delayOffset={1700}
                        highlightKeywords={keywords}
                      />
                    }
                    delay="1700ms"
                  />
                </div>
                <div className="space-y-2">
                  <div className="text-slate-500 mb-2"># HIRING_SIGNALS</div>
                  <TermRow
                    label="EST_COMP"
                    value={
                      <span className="text-emerald-400 font-bold">
                        {
                          result.hiring_and_compensation
                            ?.estimated_compensation_range
                        }
                      </span>
                    }
                    delay="2500ms"
                  />
                  <TermRow
                    label="TRENDS"
                    value={
                      <TypewriterText
                        text={
                          result.hiring_and_compensation?.fresher_hiring_trends
                        }
                        delayOffset={2600}
                        highlightKeywords={keywords}
                      />
                    }
                    delay="2600ms"
                  />
                </div>
              </div>

              <div
                className="space-y-3 term-animate"
                style={{ animationDelay: "3500ms" }}
              >
                <div className="text-cyan-600"># TECHNICAL_REQUIREMENTS</div>
                <TermRow
                  label="SYS_DESIGN"
                  value={
                    <TypewriterText
                      text={
                        result.technical_interview_focus
                          ?.system_design_expectations
                      }
                      delayOffset={3600}
                      highlightKeywords={keywords}
                    />
                  }
                  delay="3600ms"
                />
                <TermArray
                  label="DEEP_DIVES"
                  items={
                    result.technical_interview_focus?.core_tech_stack_deep_dives
                  }
                  colorClass="border-cyan-800 text-cyan-400 bg-cyan-950"
                  delay="4000ms"
                />
                <TermArray
                  label="DS_ALGO"
                  items={
                    result.technical_interview_focus
                      ?.data_structures_and_algorithms
                  }
                  colorClass="border-orange-800 text-orange-400 bg-orange-950"
                  delay="4200ms"
                />
              </div>

              <div
                className="pt-4 term-animate text-slate-500"
                style={{ animationDelay: "4500ms" }}
              >
                root_node_terminated <span className="cursor-blink"></span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Bento Grid Result Panel for the final brief, with staggered entrance animations and keyword highlighting
// import { useState, useEffect } from 'react';
// import axios from 'axios';

// // 1. Helper component for array mapping (the "Pills")
// const Badge = ({ children, colorClass = "bg-blue-100 text-blue-700" }) => (
//     <span className={`px-3 py-1 rounded-full text-xs font-semibold ${colorClass}`}>
//         {children}
//     </span>
// );

// // 2. Helper component for the Bento Grid cards
// const BentoCard = ({ title, children, delay, className = '' }) => (
//     <div
//         className={`bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 bento-animate ${className}`}
//         style={{ animationDelay: delay }}
//     >
//         <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 border-b pb-2">{title}</h4>
//         {children}
//     </div>
// );

// export default function ResultPanel({ runId, synthesizeStatus }) {
//     const [result, setResult] = useState(null);
//     const [error, setError] = useState(null);

//     useEffect(() => {
//         if (synthesizeStatus === 'done' && runId) {
//             axios.get(`${import.meta.env.VITE_API_BASE_URL}/runs/${runId}`)
//                 .then(res => {
//                     const rawResult = res.data.nodes?.synthesize?.result;
//                     // Ensure we have a JavaScript object, parsing it if the backend returned a string
//                     const parsedData = typeof rawResult === 'string' ? JSON.parse(rawResult) : rawResult;
//                     setResult(parsedData);
//                 })
//                 .catch(err => {
//                     console.error("Failed to fetch results", err);
//                     setError("Could not load final brief.");
//                 });
//         } else {
//             setResult(null);
//             setError(null);
//         }
//     }, [runId, synthesizeStatus]);

//     // 3. Keyword Highlighter Function
//     const highlightText = (text) => {
//         if (!text) return null;
//         // Add words you want to pop out automatically
//         const keywords = ['Scalability', 'System Design', 'Cloud', 'Java', 'React', 'Performance', 'Reliability', 'Innovation'];
//         const regex = new RegExp(`(${keywords.join('|')})`, 'gi');
//         const parts = text.split(regex);

//         return parts.map((part, i) =>
//             keywords.some(k => k.toLowerCase() === part.toLowerCase())
//                 ? <span key={i} className="text-indigo-600 font-semibold bg-indigo-50 px-1 rounded-sm">{part}</span>
//                 : part
//         );
//     };

//     if (synthesizeStatus !== 'done') return null;

//     return (
//         <div className="mt-8 pt-8 border-t-2 border-slate-200">
//             {/* Injecting custom keyframe for the staggered entrance */}
//             <style>{`
//                 @keyframes fadeInUp {
//                     from { opacity: 0; transform: translateY(20px); }
//                     to { opacity: 1; transform: translateY(0); }
//                 }
//                 .bento-animate {
//                     opacity: 0;
//                     animation: fadeInUp 0.6s ease-out forwards;
//                 }
//             `}</style>

//             <h3 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-3">
//                 <span className="text-3xl">✨</span> Intelligence Brief
//             </h3>

//             {error ? (
//                 <div className="text-red-600 bg-red-50 p-4 rounded-lg">{error}</div>
//             ) : result ? (
//                 <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

//                     {/* Feature Card: Strategic Advice (Spans full width) */}
//                     <BentoCard title="Strategic Interview Advice" delay="0ms" className="md:col-span-3 bg-gradient-to-br from-indigo-50 to-white border-indigo-100">
//                         <p className="text-slate-700 leading-relaxed text-lg">
//                             {highlightText(result.strategic_interview_advice)}
//                         </p>
//                     </BentoCard>

//                     {/* Left Col: Market */}
//                     <BentoCard title="Market & Competition" delay="100ms">
//                         <p className="text-sm text-slate-600 mb-4 leading-relaxed">
//                             {highlightText(result.market_and_competition?.market_position_and_challenges)}
//                         </p>
//                         <div className="flex flex-wrap gap-2">
//                             {result.market_and_competition?.direct_competitors?.map(comp => (
//                                 <Badge key={comp} colorClass="bg-slate-100 text-slate-600">{comp}</Badge>
//                             ))}
//                         </div>
//                     </BentoCard>

//                     {/* Middle Col: Hiring */}
//                     <BentoCard title="Hiring Trends & Comp" delay="200ms">
//                         <div className="mb-4">
//                             <span className="block text-xs text-slate-400 font-bold mb-1">EST. COMPENSATION</span>
//                             <span className="text-2xl font-black text-emerald-600">
//                                 {result.hiring_and_compensation?.estimated_compensation_range}
//                             </span>
//                         </div>
//                         <p className="text-sm text-slate-600 leading-relaxed">
//                             {result.hiring_and_compensation?.fresher_hiring_trends}
//                         </p>
//                     </BentoCard>

//                     {/* Right Col: Tech Focus */}
//                     <BentoCard title="Technical Focus" delay="300ms">
//                         <p className="text-sm text-slate-600 mb-4 leading-relaxed">
//                             {highlightText(result.technical_interview_focus?.system_design_expectations)}
//                         </p>
//                         <div className="space-y-3">
//                             <div>
//                                 <span className="block text-xs text-slate-400 mb-1">DEEP DIVES</span>
//                                 <div className="flex flex-wrap gap-2">
//                                     {result.technical_interview_focus?.core_tech_stack_deep_dives?.map(tech => (
//                                         <Badge key={tech} colorClass="bg-orange-100 text-orange-700">{tech}</Badge>
//                                     ))}
//                                 </div>
//                             </div>
//                         </div>
//                     </BentoCard>

//                     {/* Bottom Row: Portfolio Projects (Spans full width) */}
//                     {result.recommended_portfolio_projects && result.recommended_portfolio_projects.length > 0 && (
//                         <BentoCard title="Recommended Portfolio Projects" delay="400ms" className="md:col-span-3">
//                             <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
//                                 {result.recommended_portfolio_projects.map((proj, idx) => (
//                                     <div key={idx} className="p-4 rounded-xl border border-slate-100 bg-slate-50">
//                                         <h5 className="font-bold text-slate-800 mb-2">{proj.project_title}</h5>
//                                         <p className="text-sm text-slate-600 mb-4">{proj.relevance_explanation}</p>

//                                         <div className="flex flex-wrap gap-2 mb-3">
//                                             {proj.target_tech_stack_to_use?.map(tech => (
//                                                 <Badge key={tech} colorClass="bg-sky-100 text-sky-700">{tech}</Badge>
//                                             ))}
//                                         </div>
//                                         <div className="text-xs text-slate-500 flex flex-wrap gap-x-3 gap-y-1">
//                                             <span className="font-bold text-slate-400">FEATURES:</span>
//                                             {proj.core_features?.join(" • ")}
//                                         </div>
//                                     </div>
//                                 ))}
//                             </div>
//                         </BentoCard>
//                     )}

//                 </div>
//             ) : (
//                 <div className="flex items-center justify-center p-12 text-slate-400 animate-pulse">
//                     <svg className="w-6 h-6 animate-spin mr-3" fill="none" viewBox="0 0 24 24">
//                         <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
//                         <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
//                     </svg>
//                     Compiling visual brief...
//                 </div>
//             )}
//         </div>
//     );
// }
