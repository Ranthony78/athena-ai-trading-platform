// Get signal color class
export const getSignalColor = (signal) => {
    const colors = {
        BUY: "text-green-400",
        SELL: "text-red-400",
        NEUTRAL: "text-dark-400",
        NO_SETUP: "text-dark-400",
        WATCH: "text-yellow-400",
    };
    return colors[signal] || "text-dark-400";
};

// Get signal badge class
export const getSignalBadge = (signal) => {
    const badges = {
        BUY: "badge-green",
        SELL: "badge-red",
        NEUTRAL: "badge-gray",
        NO_SETUP: "badge-gray",
        WATCH: "badge-yellow",
    };
    return badges[signal] || "badge-gray";
};

// Get confidence color
export const getConfidenceColor = (confidence) => {
    const colors = {
        HIGH: "text-green-400",
        MEDIUM: "text-yellow-400",
        LOW: "text-red-400",
    };
    return colors[confidence] || "text-dark-400";
};

// Get session color
export const getSessionColor = (session) => {
    const colors = {
        LIVE: "text-green-400",
        PRE_OPEN: "text-yellow-400",
        CLOSED: "text-dark-400",
        HOLIDAY: "text-dark-500",
    };
    return colors[session] || "text-dark-400";
};

// Clamp value
export const clamp = (value, min, max) =>
    Math.min(Math.max(value, min), max);

// Truncate text
export const truncate = (text, maxLength = 100) => {
    if (!text) return "";
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
};

// Debounce
export const debounce = (fn, delay) => {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
};

// Group array by key
export const groupBy = (array, key) =>
    array.reduce((result, item) => {
        const group = item[key];
        if (!result[group]) result[group] = [];
        result[group].push(item);
        return result;
    }, {});

// Sort array by key
export const sortBy = (array, key, direction = "asc") =>
    [...array].sort((a, b) => {
        if (direction === "asc") return a[key] > b[key] ? 1 : -1;
        return a[key] < b[key] ? 1 : -1;
    });

// Check if market is open (IST)
export const isMarketOpen = () => {
    const now = new Date();
    const ist = new Date(
        now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" })
    );
    const day = ist.getDay();
    const hours = ist.getHours();
    const minutes = ist.getMinutes();
    const time = hours * 60 + minutes;

    if (day === 0 || day === 6) return false;
    return time >= 555 && time <= 930; // 9:15 to 15:30
};