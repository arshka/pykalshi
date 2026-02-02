/**
 * useMarketFeed - Custom hook for real-time market data via WebSocket
 *
 * Manages WebSocket connection to the market feed proxy, handling:
 * - Connection lifecycle and reconnection with exponential backoff
 * - Orderbook state (snapshots + deltas)
 * - Live ticker updates (price, volume, OI, bid/ask)
 */
function useMarketFeed(ticker) {
    const [orderbook, setOrderbook] = useState({ yes: [], no: [] });
    const [connected, setConnected] = useState(false);
    const [liveData, setLiveData] = useState({
        price: null,
        volume: null,
        openInterest: null,
        yesBid: null,
        yesAsk: null,
    });

    useEffect(() => {
        if (!ticker) return;

        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/market/${ticker}`;

        let ws = null;
        let reconnectTimeout = null;
        let reconnectDelay = 1000;
        const orderbookState = { yes: new Map(), no: new Map() };

        const updateOrderbookDisplay = () => {
            setOrderbook({
                yes: Array.from(orderbookState.yes.entries()),
                no: Array.from(orderbookState.no.entries())
            });
        };

        const handleMessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                const msgType = data.type;
                const msg = data.msg || {};

                if (msgType === 'orderbook_snapshot') {
                    orderbookState.yes = new Map((msg.yes || []).map(([p, q]) => [p, q]));
                    orderbookState.no = new Map((msg.no || []).map(([p, q]) => [p, q]));
                    updateOrderbookDisplay();
                }
                else if (msgType === 'orderbook_delta') {
                    const side = msg.side === 'yes' ? 'yes' : 'no';
                    const currentQty = orderbookState[side].get(msg.price) || 0;
                    const newQty = currentQty + msg.delta;

                    if (newQty <= 0) {
                        orderbookState[side].delete(msg.price);
                    } else {
                        orderbookState[side].set(msg.price, newQty);
                    }
                    updateOrderbookDisplay();
                }
                else if (msgType === 'ticker') {
                    setLiveData(prev => ({
                        price: msg.price ?? prev.price,
                        volume: msg.volume ?? prev.volume,
                        openInterest: msg.open_interest ?? prev.openInterest,
                        yesBid: msg.yes_bid ?? prev.yesBid,
                        yesAsk: msg.yes_ask ?? prev.yesAsk,
                    }));
                }
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };

        const connect = () => {
            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log(`WebSocket connected for ${ticker}`);
                setConnected(true);
                reconnectDelay = 1000;
            };

            ws.onclose = (e) => {
                console.log(`WebSocket closed for ${ticker}`, e.code);
                setConnected(false);
                if (!e.wasClean) {
                    reconnectTimeout = setTimeout(connect, reconnectDelay);
                    reconnectDelay = Math.min(reconnectDelay * 2, 30000);
                }
            };

            ws.onerror = (e) => {
                console.error('WebSocket error:', e);
            };

            ws.onmessage = handleMessage;
        };

        connect();

        return () => {
            if (reconnectTimeout) clearTimeout(reconnectTimeout);
            if (ws) {
                ws.onclose = null; // Prevent reconnect on intentional close
                ws.close();
            }
        };
    }, [ticker]);

    return { orderbook, connected, liveData };
}
