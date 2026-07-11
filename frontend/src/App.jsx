import "./App.css";

const phaseZeroChecks = [
  "backend and frontend folders exist",
  "backend requirements were already installed",
  "frontend scaffold has been replaced with a Threadwright landing page",
  "Tailwind utility classes are used for the visible red test block",
];

function App() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-10 lg:px-10">
        <header className="flex flex-col gap-6 border-b border-white/10 pb-8">
          <div className="inline-flex w-fit items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.24em] text-emerald-300">
            Threadwright Phase 0
          </div>
          <div className="max-w-3xl space-y-4">
            <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-6xl">
              Async DAG orchestration with a live demo surface.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
              This starter view marks the Phase 0 frontend as wired up and gives
              you a visible Tailwind test target while the backend scheduler is
              still being built.
            </p>
          </div>
        </header>

        <section className="grid flex-1 gap-6 py-8 lg:grid-cols-[1.2fr_0.8fr]">
          <article className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur">
            <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-5">
              <div>
                <h2 className="text-xl font-semibold text-white">
                  Phase 0 checklist
                </h2>
                <p className="mt-1 text-sm text-slate-400">
                  The items below reflect the current workspace state.
                </p>
              </div>
              <div className="rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-xs font-medium text-amber-200">
                Frontend ready
              </div>
            </div>

            <ul className="mt-5 space-y-3 text-sm text-slate-200">
              {phaseZeroChecks.map((item) => (
                <li
                  key={item}
                  className="flex items-start gap-3 rounded-2xl bg-slate-900/70 px-4 py-3 ring-1 ring-white/5"
                >
                  <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-400/20 text-[10px] font-bold text-emerald-300">
                    ✓
                  </span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>

            <div className="mt-6 flex flex-wrap gap-3 text-xs text-slate-400">
              <span className="rounded-full border border-white/10 px-3 py-1">
                React
              </span>
              <span className="rounded-full border border-white/10 px-3 py-1">
                Vite
              </span>
              <span className="rounded-full border border-white/10 px-3 py-1">
                Tailwind
              </span>
              <span className="rounded-full border border-white/10 px-3 py-1">
                Workspace scaffold
              </span>
            </div>
          </article>

          <aside className="grid gap-6">
            <div className="rounded-3xl border border-white/10 bg-slate-900/80 p-6">
              <h2 className="text-xl font-semibold text-white">
                Tailwind test block
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                This red tile is the explicit Phase 0 visual check.
              </p>
              <div className="mt-5 rounded-2xl border border-white/10 bg-slate-950/70 p-4">
                <div className="h-24 w-full rounded-2xl bg-red-500 shadow-[0_0_0_1px_rgba(255,255,255,0.08)]" />
              </div>
            </div>

            <div className="rounded-3xl border border-cyan-400/20 bg-cyan-400/5 p-6">
              <h3 className="text-lg font-semibold text-white">Next check</h3>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                Once the backend starts, this page can be replaced by the
                workflow run UI without changing the project scaffold.
              </p>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}

export default App;
