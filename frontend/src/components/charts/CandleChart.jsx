import { useEffect, useMemo, useRef, useState } from "react";
import { CandlestickSeries, ColorType, createChart, LineSeries } from "lightweight-charts";

function formatMarketDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return new Intl.DateTimeFormat("en-IN", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).format(date);
}

function formatMarketTime(timestamp) {
    return new Intl.DateTimeFormat("en-IN", {
        timeZone: "Asia/Kolkata",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    }).format(new Date(Number(timestamp) * 1000));
}

function toChartData(points) {
    const unique = new Map();
    points.forEach((candle) => {
        const timestamp = Math.floor(new Date(candle.candle_time).getTime() / 1000);
        if (Number.isFinite(timestamp)) {
            unique.set(timestamp, {
                time: timestamp,
                open: Number(candle.open),
                high: Number(candle.high),
                low: Number(candle.low),
                close: Number(candle.close),
            });
        }
    });
    return [...unique.values()].sort((a, b) => a.time - b.time);
}

function formatPrice(value) {
    return Number(value).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function CandleChart({ candles = [], currentPrice, interval = "15m" }) {
    const hostRef = useRef(null);
    const chartRef = useRef(null);
    const candleSeriesRef = useRef(null);
    const lineSeriesRef = useRef(null);
    const priceLineRef = useRef(null);
    const latestCandleRef = useRef(null);
    const lastIntervalRef = useRef(null);
    const [chartType, setChartType] = useState("candles");
    const [hoveredCandle, setHoveredCandle] = useState(null);

    const points = useMemo(() => {
        const valid = candles
            .filter((candle) => [candle.open, candle.high, candle.low, candle.close]
                .every((value) => Number.isFinite(Number(value))))
            .sort((a, b) => new Date(a.candle_time) - new Date(b.candle_time));
        const latestDate = valid.length ? formatMarketDate(valid[valid.length - 1].candle_time) : "";
        return valid.filter((candle) => formatMarketDate(candle.candle_time) === latestDate);
    }, [candles]);
    const chartData = useMemo(() => toChartData(points), [points]);
    const intervalMinutes = Number.parseInt(interval, 10) || 15;

    useEffect(() => {
        const host = hostRef.current;
        if (!host) return undefined;

        const readTheme = () => {
            const styles = getComputedStyle(document.documentElement);
            return {
                gridColor: styles.getPropertyValue("--chart-grid").trim() || "#334155",
                textColor: styles.getPropertyValue("--chart-label").trim() || "#94a3b8",
                accentColor: styles.getPropertyValue("--chart-accent").trim() || "#60a5fa",
                background: getComputedStyle(host).backgroundColor || "#111827",
            };
        };
        const theme = readTheme();
        const chart = createChart(host, {
            width: host.clientWidth,
            height: 340,
            layout: {
                background: { type: ColorType.Solid, color: theme.background },
                textColor: theme.textColor,
                fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
                attributionLogo: true,
            },
            grid: {
                vertLines: { color: theme.gridColor },
                horzLines: { color: theme.gridColor },
            },
            rightPriceScale: { borderColor: theme.gridColor, scaleMargins: { top: 0.12, bottom: 0.12 } },
            timeScale: {
                borderColor: theme.gridColor,
                timeVisible: true,
                secondsVisible: false,
                tickMarkFormatter: (time) => typeof time === "number" ? formatMarketTime(time) : "",
            },
            localization: {
                locale: "en-IN",
                timeFormatter: (time) => typeof time === "number"
                    ? `${formatMarketDate(new Date(time * 1000).toISOString())} ${formatMarketTime(time)} IST`
                    : "",
            },
            crosshair: { mode: 0 },
            handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false },
            handleScale: { axisPressedMouseMove: true, mouseWheel: true, pinch: true },
        });
        const candleSeries = chart.addSeries(CandlestickSeries, {
            upColor: "#22c55e",
            downColor: "#ef4444",
            borderVisible: false,
            wickUpColor: "#22c55e",
            wickDownColor: "#ef4444",
            priceLineVisible: false,
            lastValueVisible: false,
        });
        const lineSeries = chart.addSeries(LineSeries, {
            color: theme.accentColor,
            lineWidth: 2,
            priceLineVisible: false,
            lastValueVisible: false,
        });
        const resizeObserver = new ResizeObserver(([entry]) => {
            if (entry?.contentRect.width) chart.applyOptions({ width: Math.floor(entry.contentRect.width) });
        });
        resizeObserver.observe(host);

        const themeObserver = new MutationObserver(() => {
            const next = readTheme();
            chart.applyOptions({
                layout: { background: { type: ColorType.Solid, color: next.background }, textColor: next.textColor },
                grid: { vertLines: { color: next.gridColor }, horzLines: { color: next.gridColor } },
                rightPriceScale: { borderColor: next.gridColor },
                timeScale: { borderColor: next.gridColor },
            });
            lineSeries.applyOptions({ color: next.accentColor });
            if (priceLineRef.current) priceLineRef.current.applyOptions({ color: next.accentColor });
        });
        themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

        chart.subscribeCrosshairMove((param) => {
            const hovered = param.seriesData.get(candleSeries);
            if (hovered && "open" in hovered) setHoveredCandle(hovered);
            else setHoveredCandle(null);
        });

        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;
        lineSeriesRef.current = lineSeries;
        return () => {
            themeObserver.disconnect();
            resizeObserver.disconnect();
            chart.remove();
            chartRef.current = null;
            candleSeriesRef.current = null;
            lineSeriesRef.current = null;
            priceLineRef.current = null;
            // React StrictMode remounts effects in development. Reset this so
            // the replacement chart also performs its initial fit-to-data.
            latestCandleRef.current = null;
            lastIntervalRef.current = null;
        };
    }, []);

    useEffect(() => {
        const candleSeries = candleSeriesRef.current;
        const lineSeries = lineSeriesRef.current;
        const chart = chartRef.current;
        if (!candleSeries || !lineSeries || !chart) return;

        const previousLatest = latestCandleRef.current;
        const intervalChanged = lastIntervalRef.current !== interval;
        candleSeries.setData(chartData);
        lineSeries.setData(chartData.map(({ time, close }) => ({ time, value: close })));
        latestCandleRef.current = chartData[chartData.length - 1] ?? null;
        lastIntervalRef.current = interval;

        if (intervalChanged && chartData.length) {
            chart.timeScale().fitContent();
        } else if (previousLatest && chartData.length && previousLatest.time !== chartData[chartData.length - 1].time) {
            chart.timeScale().scrollToRealTime();
        }
    }, [chartData, interval]);

    useEffect(() => {
        const chart = chartRef.current;
        const candleSeries = candleSeriesRef.current;
        if (!chart || !candleSeries) return;

        const price = Number(currentPrice);
        if (Number.isFinite(price) && price > 0) {
            if (priceLineRef.current) {
                priceLineRef.current.applyOptions({ price });
            } else {
                const accent = getComputedStyle(document.documentElement).getPropertyValue("--chart-accent").trim() || "#60a5fa";
                priceLineRef.current = candleSeries.createPriceLine({
                    price,
                    color: accent,
                    lineWidth: 1,
                    lineStyle: 2,
                    axisLabelVisible: true,
                    title: "LTP",
                });
            }
        }
    }, [currentPrice]);

    const toggleChartType = (type) => {
        setChartType(type);
        candleSeriesRef.current?.applyOptions({ visible: type === "candles" });
        lineSeriesRef.current?.applyOptions({ visible: type === "line" });
    };
    const displayCandle = hoveredCandle || chartData[chartData.length - 1];

    if (chartData.length < 2) {
        return (
            <div className="flex min-h-64 items-center justify-center rounded-lg bg-dark-950 px-5 text-center text-sm text-dark-500">
                Chart needs at least two stored {intervalMinutes}-minute candles from the latest available trading session.
            </div>
        );
    }

    return (
        <div className="overflow-hidden rounded-lg border border-dark-700 bg-dark-950" aria-label={`NIFTY ${chartType === "candles" ? "candlestick" : "line"} chart`}>
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-dark-800 px-3 py-2.5">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-xs" aria-live="polite">
                    <span className="font-sans font-semibold text-dark-400">{hoveredCandle ? formatMarketTime(hoveredCandle.time) : "O H L C"}</span>
                    {displayCandle && <>
                        <span className="text-dark-300">O <b className="text-dark-100">{formatPrice(displayCandle.open)}</b></span>
                        <span className="text-dark-300">H <b className="text-green-500">{formatPrice(displayCandle.high)}</b></span>
                        <span className="text-dark-300">L <b className="text-red-500">{formatPrice(displayCandle.low)}</b></span>
                        <span className="text-dark-300">C <b className="text-dark-100">{formatPrice(displayCandle.close)}</b></span>
                    </>}
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex rounded-md border border-dark-700 p-0.5" role="group" aria-label="Chart type">
                        {[{ value: "candles", label: "Candles" }, { value: "line", label: "Line" }].map((item) => (
                            <button
                                key={item.value}
                                type="button"
                                onClick={() => toggleChartType(item.value)}
                                aria-pressed={chartType === item.value}
                                className={`rounded px-2.5 py-1 text-xs font-medium transition ${chartType === item.value ? "bg-dark-700 text-dark-50" : "text-dark-400 hover:text-dark-100"}`}
                            >{item.label}</button>
                        ))}
                    </div>
                    <button
                        type="button"
                        onClick={() => chartRef.current?.timeScale().fitContent()}
                        className="rounded-md border border-dark-700 px-2.5 py-1.5 text-xs font-medium text-dark-300 hover:bg-dark-800 hover:text-dark-50"
                    >Reset view</button>
                </div>
            </div>
            <div ref={hostRef} className="h-[340px] w-full bg-dark-950" role="img" aria-label={`Interactive NIFTY chart with ${chartData.length} ${intervalMinutes}-minute candles. Use the mouse wheel or pinch to zoom, and drag to pan.`} />
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-dark-800 px-3 py-2 text-[11px] text-dark-500">
                <span>{points.length} candles · India Standard Time · Drag to pan · Scroll to zoom</span>
                <a href="https://www.tradingview.com/" target="_blank" rel="noreferrer" className="font-medium text-dark-400 hover:text-dark-200">Charting by TradingView</a>
            </div>
        </div>
    );
}
