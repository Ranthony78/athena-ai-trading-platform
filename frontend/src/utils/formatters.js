// Currency formatter (INR)
export const formatCurrency = (value, decimals = 2) => {
    if (value === null || value === undefined) return "—";
    const num = parseFloat(value);
    if (isNaN(num)) return "—";

    const abs = Math.abs(num);
    let formatted;

    if (abs >= 10000000) {
        formatted = (num / 10000000).toFixed(2) + " Cr";
    } else if (abs >= 100000) {
        formatted = (num / 100000).toFixed(2) + " L";
    } else if (abs >= 1000) {
        formatted = (num / 1000).toFixed(2) + " K";
    } else {
        formatted = num.toFixed(decimals);
    }

    return `₹${formatted}`;
};

// Raw number formatter
export const formatNumber = (value, decimals = 2) => {
    if (value === null || value === undefined) return "—";
    const num = parseFloat(value);
    if (isNaN(num)) return "—";
    return num.toLocaleString("en-IN", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
};

// Percentage formatter
export const formatPercent = (value, decimals = 2) => {
    if (value === null || value === undefined) return "—";
    const num = parseFloat(value);
    if (isNaN(num)) return "—";
    const sign = num > 0 ? "+" : "";
    return `${sign}${num.toFixed(decimals)}%`;
};

// PnL formatter — returns value + color class
export const formatPnL = (value) => {
    if (value === null || value === undefined) return { text: "—", color: "neutral" };
    const num = parseFloat(value);
    if (isNaN(num)) return { text: "—", color: "neutral" };

    return {
        text: formatCurrency(Math.abs(num)),
        color: num > 0 ? "positive" : num < 0 ? "negative" : "neutral",
        sign: num > 0 ? "+" : num < 0 ? "-" : "",
    };
};

// Date formatter
export const formatDate = (date) => {
    if (!date) return "—";
    return new Date(date).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    });
};

// Time formatter
export const formatTime = (date) => {
    if (!date) return "—";
    return new Date(date).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
    });
};

// DateTime formatter
export const formatDateTime = (date) => {
    if (!date) return "—";
    return `${formatDate(date)} ${formatTime(date)}`;
};

// Relative time
export const formatRelativeTime = (date) => {
    if (!date) return "—";
    const now = new Date();
    const d = new Date(date);
    const diff = Math.floor((now - d) / 1000);

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return formatDate(date);
};

// Large number abbreviation
export const abbreviateNumber = (value) => {
    if (!value) return "0";
    const num = parseFloat(value);
    if (num >= 10000000) return (num / 10000000).toFixed(1) + "Cr";
    if (num >= 100000) return (num / 100000).toFixed(1) + "L";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toString();
};