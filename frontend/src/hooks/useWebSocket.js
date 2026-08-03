import { useEffect, useRef, useCallback } from "react";
import useAuthStore from "../store/authStore";
import useMarketStore from "../store/marketStore";

export function useMarketWebSocket(symbol = null) {
    const ws = useRef(null);
    const { accessToken } = useAuthStore();
    const { setQuote, setSession } = useMarketStore();

    const connect = useCallback(() => {
        const url = symbol
            ? `ws://127.0.0.1:8000/ws/market/quotes/${symbol}/`
            : `ws://127.0.0.1:8000/ws/market/quotes/`;

        ws.current = new WebSocket(url);

        ws.current.onopen = () => {
            console.log("WebSocket connected");
        };

        ws.current.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);

                if (message.type === "tick") {
                    const tick = message.data;
                    setQuote(tick.symbol, tick);
                }

                if (message.type === "session") {
                    setSession(message.data);
                }
            } catch (e) {
                console.error("WebSocket parse error:", e);
            }
        };

        ws.current.onclose = () => {
            console.log("WebSocket closed — reconnecting in 5s");
            setTimeout(connect, 5000);
        };

        ws.current.onerror = (error) => {
            console.error("WebSocket error:", error);
        };
    }, [symbol, setQuote, setSession]);

    useEffect(() => {
        if (accessToken) {
            connect();
        }

        return () => {
            if (ws.current) {
                ws.current.onclose = null;
                ws.current.close();
            }
        };
    }, [connect, accessToken]);

    const sendMessage = useCallback((message) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(message));
        }
    }, []);

    return { sendMessage };
}