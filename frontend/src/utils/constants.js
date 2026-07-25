export const APP_NAME = "Athena AI";
export const APP_VERSION = "1.0.0";

export const TIMEFRAMES = [
    { value: "1m", label: "1 Min" },
    { value: "3m", label: "3 Min" },
    { value: "5m", label: "5 Min" },
    { value: "15m", label: "15 Min" },
    { value: "30m", label: "30 Min" },
    { value: "1h", label: "1 Hour" },
    { value: "1d", label: "1 Day" },
];

export const INDICES = [
    "NIFTY",
    "BANKNIFTY",
    "FINNIFTY",
    "MIDCPNIFTY",
];

export const EXCHANGES = [
    { value: "NSE", label: "NSE" },
    { value: "BSE", label: "BSE" },
    { value: "NFO", label: "NFO" },
    { value: "MCX", label: "MCX" },
];

export const SIGNAL_COLORS = {
    BUY: "text-green-400",
    SELL: "text-red-400",
    NEUTRAL: "text-dark-400",
    NO_SETUP: "text-dark-400",
    WATCH: "text-yellow-400",
};

export const SIGNAL_BADGES = {
    BUY: "badge-green",
    SELL: "badge-red",
    NEUTRAL: "badge-gray",
    NO_SETUP: "badge-gray",
    WATCH: "badge-yellow",
};

export const CONFIDENCE_COLORS = {
    HIGH: "text-green-400",
    MEDIUM: "text-yellow-400",
    LOW: "text-red-400",
};

export const SESSION_COLORS = {
    LIVE: "text-green-400",
    PRE_OPEN: "text-yellow-400",
    CLOSED: "text-dark-400",
};

export const INDICATORS = [
    "EMA_9",
    "EMA_21",
    "EMA_50",
    "RSI_14",
    "MACD",
    "BB_20",
    "VWAP",
    "ATR_14",
    "CPR",
];