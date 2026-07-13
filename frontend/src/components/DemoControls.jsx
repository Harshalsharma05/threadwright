export default function DemoControls({ injectFailure, setInjectFailure }) {
    return (
        <div className="flex items-center gap-4 bg-red-50 p-4 rounded-lg border border-red-100 mb-6">
            <label className="flex items-center gap-2 cursor-pointer">
                <input 
                    type="checkbox" 
                    checked={injectFailure}
                    onChange={(e) => setInjectFailure(e.target.checked)}
                    className="w-4 h-4 text-red-600 rounded border-red-300 focus:ring-red-500"
                />
                <span className="text-sm font-semibold text-red-900">
                    Inject API Failure (search_news)
                </span>
            </label>
            <span className="text-xs text-red-700">
                Forces the news node to crash initially to demonstrate exponential backoff & retries.
            </span>
        </div>
    );
}