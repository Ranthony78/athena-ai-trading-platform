// Display helpers for the market workspaces. Every one returns "NA" for a
// missing or non-numeric value, so a gap in the data is never shown as 0.

const toNumber = (value) => {
    if (value === null || value === undefined || value === "") return null;
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
};

export const num = (value, decimals = 2) => {
    const number = toNumber(value);
    if (number === null) return "NA";
    return number.toLocaleString("en-IN", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
};

export const whole = (value) => num(value, 0);

export const signed = (value, decimals = 2) => {
    const number = toNumber(value);
    if (number === null) return "NA";
    return `${number > 0 ? "+" : ""}${num(number, decimals)}`;
};

export const percent = (value, decimals = 2) => {
    const number = toNumber(value);
    if (number === null) return "NA";
    return `${number > 0 ? "+" : ""}${number.toFixed(decimals)}%`;
};

// Indian-style compact quantity: 24,40,000 -> "24.40 lakh".
export const lakh = (value) => {
    const number = toNumber(value);
    if (number === null) return "NA";
    if (number >= 10000000) return `${(number / 10000000).toFixed(2)} cr`;
    if (number >= 100000) return `${(number / 100000).toFixed(2)} lakh`;
    return whole(number);
};

// The AI result lists evidence as strings, but tolerate small objects too.
export const toLines = (value) => {
    if (!Array.isArray(value)) return [];
    return value
        .map((item) => {
            if (typeof item === "string") return item;
            if (item && typeof item === "object") {
                return item.text || item.reason || item.summary || item.description || null;
            }
            return null;
        })
        .filter(Boolean);
};

export const isNumber = (value) => toNumber(value) !== null;
export { toNumber };
