const SimpleChart = ({ ticker }) => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [timeframe, setTimeframe] = useState('1W');
    const [hoverIndex, setHoverIndex] = useState(null);

    useEffect(() => {
        if (!ticker) return;
        setLoading(true);
        setData([]);

        let period = 'hour';
        let limit = 168;

        if (timeframe === '2H') {
            period = 'minute';
            limit = 120;
        } else if (timeframe === '1D') {
            period = 'minute';
            limit = 1440;
        } else if (timeframe === '1W') {
            period = 'hour';
            limit = 168;
        } else if (timeframe === '1M') {
            period = 'hour';
            limit = 744;
        } else if (timeframe === 'ALL') {
            period = 'day';
            limit = 3650;
        }

        fetch(`/api/markets/${ticker}/candlesticks?period=${period}&limit=${limit}`)
            .then(res => res.json())
            .then(raw => {
                const sorted = raw.sort((a, b) => a.ts - b.ts);
                setData(sorted);
                setLoading(false);
            })
            .catch(e => setLoading(false));
    }, [ticker, timeframe]);

    const formatAxisDate = (ts) => {
        const d = new Date(ts * 1000);
        if (timeframe === '2H' || timeframe === '1D') return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        return d.toLocaleDateString([], { month: 'numeric', day: 'numeric' });
    };

    if (loading) return <div className="h-full flex items-center justify-center text-zinc-600 text-xs uppercase animate-pulse">Loading Chart...</div>;

    if (!data.length) return (
        <div className="h-full flex flex-col items-center justify-center text-zinc-600 text-xs uppercase relative">
            <div className="absolute top-2 right-4 flex gap-2">
                {['2H', '1D', '1W', '1M', 'ALL'].map(tf => (
                    <button
                        key={tf}
                        onClick={() => setTimeframe(tf)}
                        className={`text-[10px] font-bold px-2 py-1 rounded transition-colors ${timeframe === tf ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}
                    >
                        {tf}
                    </button>
                ))}
            </div>
            No Data Available for {timeframe}
        </div>
    );

    const width = 1000;
    const height = 400;

    const prices = data.map(d => d.price);
    let minPrice = Math.min(...prices);
    let maxPrice = Math.max(...prices);
    const buffer = (maxPrice - minPrice) * 0.1 || 1;
    const domainMin = Math.max(0, Math.floor(minPrice - buffer));
    const domainMax = Math.min(100, Math.ceil(maxPrice + buffer));
    const priceRange = domainMax - domainMin || 1;

    const volumes = data.map(d => d.volume || 0);
    const maxVolume = Math.max(...volumes) || 1;
    const volumeHeight = height * 0.25;

    const getX = (i) => (i / Math.max(1, data.length - 1)) * width;
    const getY = (p) => (height - volumeHeight) - ((p - domainMin) / priceRange) * (height - volumeHeight - 20);

    const points = data.map((d, i) => `${getX(i)},${getY(d.price)}`).join(' ');

    const startPrice = data[0].price;
    const endPrice = data[data.length - 1].price;
    const isPositive = endPrice >= startPrice;
    const strokeColor = isPositive ? '#4ade80' : '#f87171';
    const fillColor = isPositive ? 'url(#gradGreen)' : 'url(#gradRed)';
    const volumeColor = isPositive ? '#4ade80' : '#f87171';

    const areaPath = `
        M 0,${height - volumeHeight}
        L 0,${getY(startPrice)}
        ${points.replace(/,/g, ' ')}
        L ${width},${height - volumeHeight}
        Z
    `;

    const gridLines = [0, 0.25, 0.5, 0.75, 1].map(ratio => {
        const val = domainMin + (priceRange * ratio);
        return { val: Math.round(val), y: getY(val) };
    });

    const currentDataPoint = hoverIndex !== null ? data[hoverIndex] : data[data.length - 1];
    const currentPrice = currentDataPoint ? currentDataPoint.price : endPrice;
    const currentVol = currentDataPoint ? currentDataPoint.volume : (data[data.length - 1].volume || 0);
    const currentDate = hoverIndex !== null
        ? new Date(data[hoverIndex].ts * 1000)
        : null;

    const displayDate = currentDate
        ? (timeframe === '2H' || timeframe === '1D'
            ? currentDate.toLocaleTimeString()
            : currentDate.toLocaleDateString() + ' ' + currentDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
        : `${formatAxisDate(data[0].ts)} - ${formatAxisDate(data[data.length - 1].ts)}`;

    return (
        <div className="w-full h-full relative group pt-4 pb-4 pl-4 pr-10 flex flex-col">
            <div className="flex justify-between items-start mb-2 z-10 relative">
                <div className="flex flex-col">
                    <span className={`text-2xl font-mono tracking-tight font-bold ${isPositive ? "text-green-400" : "text-red-400"}`}>
                        {formatPrice(currentPrice)}
                    </span>
                    <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-bold">
                        {displayDate} <span className="ml-2 text-zinc-600">VOL: {formatNumber(currentVol)}</span>
                    </span>
                </div>
                <div className="flex gap-1 bg-[#18181b] p-1 rounded-lg border border-zinc-800">
                    {['2H', '1D', '1W', '1M', 'ALL'].map(tf => (
                        <button
                            key={tf}
                            onClick={() => setTimeframe(tf)}
                            className={`text-[10px] font-bold px-2 py-1 rounded transition-colors ${timeframe === tf ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}
                        >
                            {tf}
                        </button>
                    ))}
                </div>
            </div>

            <div className="flex-1 relative cursor-crosshair overflow-visible">
                <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible" preserveAspectRatio="none"
                    onMouseLeave={() => setHoverIndex(null)}
                    onMouseMove={(e) => {
                        const rect = e.currentTarget.getBoundingClientRect();
                        const x = e.clientX - rect.left;
                        const ratio = Math.max(0, Math.min(1, x / rect.width));
                        const idx = Math.floor(ratio * (data.length - 1));
                        setHoverIndex(idx);
                    }}
                >
                    <defs>
                        <linearGradient id="gradGreen" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="#4ade80" stopOpacity="0.2" />
                            <stop offset="100%" stopColor="#4ade80" stopOpacity="0" />
                        </linearGradient>
                        <linearGradient id="gradRed" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="#f87171" stopOpacity="0.2" />
                            <stop offset="100%" stopColor="#f87171" stopOpacity="0" />
                        </linearGradient>
                    </defs>

                    {data.map((d, i) => {
                        let barHeight = 0;
                        if (maxVolume > 0) {
                            barHeight = ((d.volume || 0) / maxVolume) * volumeHeight;
                        }
                        const barWidth = width / data.length;
                        return (
                            <rect
                                key={i}
                                x={getX(i) - (barWidth / 2)}
                                y={height - barHeight}
                                width={Math.max(1, barWidth - 1)}
                                height={barHeight}
                                fill={volumeColor}
                                opacity={hoverIndex === i ? 0.3 : 0.1}
                            />
                        );
                    })}

                    {gridLines.map((line, i) => (
                        <g key={i}>
                            <line x1="0" y1={line.y} x2={width} y2={line.y} stroke="#27272a" strokeWidth="1" strokeDasharray="4 4" vectorEffect="non-scaling-stroke" />
                            <text x={width + 8} y={line.y + 4} fill="#52525b" fontSize="12" fontFamily="monospace" textAnchor="start" pointerEvents="none">
                                {line.val}¢
                            </text>
                        </g>
                    ))}

                    <path d={areaPath} fill={fillColor} stroke="none" />

                    <polyline
                        fill="none"
                        stroke={strokeColor}
                        strokeWidth="2"
                        points={points}
                        vectorEffect="non-scaling-stroke"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />

                    {hoverIndex !== null && (
                        <line
                            x1={getX(hoverIndex)}
                            y1="0"
                            x2={getX(hoverIndex)}
                            y2={height}
                            stroke="#71717a"
                            strokeWidth="1"
                            strokeDasharray="4 4"
                            vectorEffect="non-scaling-stroke"
                        />
                    )}
                </svg>
            </div>

            <div className="flex justify-between text-[10px] text-zinc-500 font-mono mt-2 uppercase">
                <span>{data.length > 0 && formatAxisDate(data[0].ts)}</span>
                <span>{data.length > 0 && formatAxisDate(data[data.length - 1].ts)}</span>
            </div>
        </div>
    );
};
