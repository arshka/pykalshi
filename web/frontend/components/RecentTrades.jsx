/**
 * LiveTrades Component
 *
 * Displays live trade executions for a market (last 5 minutes).
 * Fetches initial trades via REST, then receives real-time updates via WebSocket.
 * Trades expire after 5 minutes so volume stats reflect recent activity.
 */
const RecentTrades = ({ ticker, liveTrades = [] }) => {
    const [initialTrades, setInitialTrades] = useState([]);
    const [loading, setLoading] = useState(true);
    const [now, setNow] = useState(Date.now());

    // Update "now" every 5 seconds to expire old trades
    useEffect(() => {
        const interval = setInterval(() => setNow(Date.now()), 5000);
        return () => clearInterval(interval);
    }, []);

    // Fetch initial trades on mount
    useEffect(() => {
        if (!ticker) return;

        setLoading(true);
        fetch(`/api/markets/${ticker}/trades?limit=50`)
            .then(res => res.ok ? res.json() : [])
            .then(data => {
                setInitialTrades(data);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, [ticker]);

    // Merge live trades with initial, deduping by trade_id, filter to last 60 seconds
    const trades = useMemo(() => {
        const seen = new Set();
        const merged = [];
        const cutoff = now - 300000; // 5 minutes ago

        for (const t of [...liveTrades, ...initialTrades]) {
            const id = t.trade_id;
            if (id && seen.has(id)) continue;

            // Filter by time - check ts (unix seconds) or created_time
            const tradeTime = t.ts ? t.ts * 1000 : new Date(t.created_time).getTime();
            if (tradeTime < cutoff) continue;

            if (id) seen.add(id);
            merged.push(t);
        }
        return merged;
    }, [liveTrades, initialTrades, now]);

    // Calculate stats from trades
    const stats = useMemo(() => {
        if (trades.length === 0) return null;

        let yesVolume = 0;
        let noVolume = 0;
        let totalDollars = 0;

        for (const t of trades) {
            const count = t.count || 0;
            const price = t.yes_price || 50;
            const dollars = count * price; // in cents

            if (t.taker_side === 'yes') {
                yesVolume += count;
            } else if (t.taker_side === 'no') {
                noVolume += count;
            }
            totalDollars += dollars;
        }

        const totalVolume = yesVolume + noVolume;
        const yesPct = totalVolume > 0 ? (yesVolume / totalVolume) * 100 : 50;

        return {
            yesVolume,
            noVolume,
            totalVolume,
            totalDollars,
            yesPct,
        };
    }, [trades]);

    const formatTime = (ts, created_time) => {
        const date = ts ? new Date(ts * 1000) : new Date(created_time);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);

        if (diffMins < 1) return 'now';
        if (diffMins < 60) return `${diffMins}m`;
        if (diffHours < 24) return `${diffHours}h`;
        return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    };

    const formatDollars = (cents) => {
        if (cents >= 100000) return `$${(cents / 100000).toFixed(1)}k`;
        if (cents >= 10000) return `$${(cents / 100).toFixed(0)}`;
        return `$${(cents / 100).toFixed(2)}`;
    };

    return (
        <div className="bg-[#111113] rounded-xl border border-zinc-800 overflow-hidden shadow-lg">
            {/* Header with stats */}
            <div className="px-4 py-3 border-b border-zinc-800 bg-[#131316]">
                <div className="flex justify-between items-center mb-2">
                    <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Live Trades <span className="text-zinc-600 font-normal">(5m)</span></h3>
                    {stats && (
                        <div className="text-[10px] text-zinc-500 font-mono">
                            {formatNumber(stats.totalVolume)} contracts · {formatDollars(stats.totalDollars)}
                        </div>
                    )}
                </div>

                {/* Buy/Sell Pressure Bar */}
                {stats && stats.totalVolume > 0 && (
                    <div className="flex items-center gap-2">
                        <span className="text-[10px] text-green-400 font-mono w-8">{stats.yesPct.toFixed(0)}%</span>
                        <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden flex">
                            <div
                                className="h-full bg-green-500 transition-all duration-300"
                                style={{ width: `${stats.yesPct}%` }}
                            />
                            <div
                                className="h-full bg-red-500 transition-all duration-300"
                                style={{ width: `${100 - stats.yesPct}%` }}
                            />
                        </div>
                        <span className="text-[10px] text-red-400 font-mono w-8 text-right">{(100 - stats.yesPct).toFixed(0)}%</span>
                    </div>
                )}
            </div>

            <div className="max-h-[180px] overflow-y-auto custom-scrollbar">
                {loading && trades.length === 0 ? (
                    <div className="text-zinc-600 text-xs text-center py-4">Loading...</div>
                ) : trades.length === 0 ? (
                    <div className="text-zinc-600 text-xs text-center py-4">No trades in last 5 minutes</div>
                ) : (
                    <table className="w-full text-xs">
                        <thead className="sticky top-0 bg-zinc-900/90 backdrop-blur">
                            <tr className="text-[10px] uppercase text-zinc-500">
                                <th className="text-left px-3 py-2 font-medium">Time</th>
                                <th className="text-center px-2 py-2 font-medium">Side</th>
                                <th className="text-right px-2 py-2 font-medium">Price</th>
                                <th className="text-right px-2 py-2 font-medium">Qty</th>
                                <th className="text-right px-3 py-2 font-medium">Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trades.map((trade, i) => {
                                const value = (trade.count || 0) * (trade.yes_price || 0);
                                return (
                                    <tr key={trade.trade_id || i} className="hover:bg-zinc-800/30 transition-colors">
                                        <td className="px-3 py-1.5 text-zinc-500 font-mono">
                                            {formatTime(trade.ts, trade.created_time)}
                                        </td>
                                        <td className="px-2 py-1.5 text-center">
                                            <span className={`font-medium ${
                                                trade.taker_side === 'yes' ? 'text-green-400' :
                                                trade.taker_side === 'no' ? 'text-red-400' : 'text-zinc-400'
                                            }`}>
                                                {trade.taker_side?.toUpperCase() || '—'}
                                            </span>
                                        </td>
                                        <td className="px-2 py-1.5 text-right font-mono text-white">
                                            {trade.yes_price}¢
                                        </td>
                                        <td className="px-2 py-1.5 text-right font-mono text-zinc-400">
                                            {formatNumber(trade.count)}
                                        </td>
                                        <td className="px-3 py-1.5 text-right font-mono text-zinc-500">
                                            {formatDollars(value)}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};
