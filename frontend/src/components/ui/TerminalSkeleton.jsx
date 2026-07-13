import React from 'react';

// --- Skeleton Loader Component ---
export const TerminalSkeleton = () => (
    <div className="space-y-6 animate-pulse">
        <div className="w-1/3 h-4 bg-emerald-900/50 rounded mb-4"></div>
        
        <div className="border-l-2 border-indigo-900 pl-4 py-2 bg-indigo-950/10">
            <div className="w-48 h-4 bg-slate-800 rounded mb-4"></div>
            <div className="space-y-2">
                <div className="w-full h-3 bg-slate-800 rounded"></div>
                <div className="w-5/6 h-3 bg-slate-800 rounded"></div>
                <div className="w-4/6 h-3 bg-slate-800 rounded"></div>
            </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 border-y border-slate-800 py-6">
            <div className="space-y-4">
                <div className="w-40 h-4 bg-slate-800 rounded mb-2"></div>
                <div className="flex gap-4"><div className="w-24 h-3 bg-slate-800 rounded"></div><div className="w-32 h-6 bg-slate-800 rounded"></div></div>
                <div className="flex gap-4"><div className="w-24 h-3 bg-slate-800 rounded"></div><div className="w-full h-12 bg-slate-800 rounded"></div></div>
            </div>
            <div className="space-y-4">
                <div className="w-40 h-4 bg-slate-800 rounded mb-2"></div>
                <div className="flex gap-4"><div className="w-24 h-3 bg-slate-800 rounded"></div><div className="w-48 h-6 bg-emerald-900/30 rounded"></div></div>
                <div className="flex gap-4"><div className="w-24 h-3 bg-slate-800 rounded"></div><div className="w-full h-12 bg-slate-800 rounded"></div></div>
            </div>
        </div>

        <div className="space-y-4 pt-4">
            <div className="w-48 h-4 bg-slate-800 rounded mb-2"></div>
            <div className="flex gap-4"><div className="w-24 h-3 bg-slate-800 rounded"></div><div className="w-full h-8 bg-slate-800 rounded"></div></div>
            <div className="flex gap-4"><div className="w-24 h-3 bg-slate-800 rounded"></div><div className="w-3/4 h-8 bg-slate-800 rounded"></div></div>
        </div>
    </div>
);