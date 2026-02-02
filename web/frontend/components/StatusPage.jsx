const StatusPage = ({ onBack }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await fetch('/api/exchange/status');
                if (!res.ok) throw new Error('Failed to fetch status');
                const json = await res.json();
                setData(json);
            } catch (e) {
                setError(e.message);
            } finally {
                setLoading(false);
            }
        };
        fetchStatus();
        const interval = setInterval(fetchStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const formatTime = (iso) => {
        if (!iso) return '—';
        const d = new Date(iso);
        return d.toLocaleString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            timeZoneName: 'short'
        });
    };

    return (
        <div className="min-h-screen bg-[#0e0e10] p-6">
            <div className="max-w-2xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <h1 className="text-2xl font-bold text-white">Exchange Status</h1>
                    <button
                        onClick={onBack}
                        className="text-zinc-500 hover:text-white text-sm"
                    >
                        ← Back
                    </button>
                </div>

                {loading && (
                    <div className="text-zinc-500 text-center py-12">Loading...</div>
                )}

                {error && (
                    <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-red-400">
                        {error}
                    </div>
                )}

                {data && (
                    <div className="space-y-6">
                        {/* Status Card */}
                        <div className="bg-[#18181b] border border-zinc-800 rounded-xl p-6">
                            <div className="flex items-center gap-4 mb-4">
                                <div className={`w-4 h-4 rounded-full ${data.status.trading_active ? 'bg-kalshi-green animate-pulse' : 'bg-red-500'}`} />
                                <span className="text-xl font-semibold text-white">
                                    {data.status.trading_active ? 'Trading Active' : 'Trading Closed'}
                                </span>
                            </div>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="text-zinc-500">Exchange</span>
                                    <div className={data.status.exchange_active ? 'text-kalshi-green' : 'text-red-400'}>
                                        {data.status.exchange_active ? 'Online' : 'Offline'}
                                    </div>
                                </div>
                                <div>
                                    <span className="text-zinc-500">Trading</span>
                                    <div className={data.status.trading_active ? 'text-kalshi-green' : 'text-zinc-400'}>
                                        {data.status.trading_active ? 'Open' : 'Closed'}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Schedule */}
                        {data.schedule && data.schedule.length > 0 && (
                            <div className="bg-[#18181b] border border-zinc-800 rounded-xl p-6">
                                <h2 className="text-lg font-semibold text-white mb-4">Trading Schedule</h2>
                                <div className="space-y-3">
                                    {data.schedule.slice(0, 5).map((s, i) => (
                                        <div key={i} className="flex justify-between text-sm border-b border-zinc-800 pb-2 last:border-0">
                                            <span className="text-zinc-400">{formatTime(s.start_time)}</span>
                                            <span className="text-zinc-600">→</span>
                                            <span className="text-zinc-400">{formatTime(s.end_time)}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Announcements */}
                        {data.announcements && data.announcements.length > 0 && (
                            <div className="bg-[#18181b] border border-zinc-800 rounded-xl p-6">
                                <h2 className="text-lg font-semibold text-white mb-4">Announcements</h2>
                                <div className="space-y-4">
                                    {data.announcements.map((a, i) => (
                                        <div key={a.id || i} className="border-b border-zinc-800 pb-4 last:border-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="font-medium text-white">{a.title}</span>
                                                {a.type && (
                                                    <span className="text-xs bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded">
                                                        {a.type}
                                                    </span>
                                                )}
                                            </div>
                                            {a.body && <p className="text-sm text-zinc-500">{a.body}</p>}
                                            {a.created_time && (
                                                <p className="text-xs text-zinc-600 mt-1">{formatTime(a.created_time)}</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Empty announcements */}
                        {(!data.announcements || data.announcements.length === 0) && (
                            <div className="bg-[#18181b] border border-zinc-800 rounded-xl p-6">
                                <h2 className="text-lg font-semibold text-white mb-2">Announcements</h2>
                                <p className="text-zinc-500 text-sm">No announcements at this time.</p>
                            </div>
                        )}

                        <p className="text-xs text-zinc-600 text-center">
                            Auto-refreshes every 30 seconds
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};
