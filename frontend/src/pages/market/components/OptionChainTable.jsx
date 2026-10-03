import { formatNumber, abbreviateNumber } from "../../../utils/formatters";

function greek(value, decimals = 3) {
    if (
        value === null ||
        value === undefined ||
        !Number.isFinite(Number(value)) ||
        Number(value) === 0
    )
        return "—";
    return Number(value).toFixed(decimals);
}

function OptionCells({ option, side, showGreeks }) {
    const tone = side === "call" ? "text-emerald-300" : "text-rose-300";
    return (
        <>
            <td className="text-right text-dark-300">
                {option ? abbreviateNumber(option.oi) : "—"}
            </td>
            <td className="text-right text-dark-300">
                {option ? abbreviateNumber(option.volume) : "—"}
            </td>
            <td className={`text-right font-mono font-semibold ${tone}`}>
                {option ? formatNumber(option.ltp) : "—"}
            </td>
            <td className="text-right text-dark-300">
                {option && Number(option.iv) !== 0 ? `${greek(option.iv, 2)}%` : "—"}
            </td>
            {showGreeks && (
                <>
                    <td className="text-right text-dark-300">
                        {option ? greek(option.delta) : "—"}
                    </td>
                    <td className="text-right text-dark-300">
                        {option ? greek(option.gamma, 5) : "—"}
                    </td>
                    <td className="text-right text-dark-300">
                        {option ? greek(option.theta) : "—"}
                    </td>
                    <td className="text-right text-dark-300">
                        {option ? greek(option.vega) : "—"}
                    </td>
                </>
            )}
        </>
    );
}

export default function OptionChainTable({ chain = [], strikes, atmStrike, showGreeks = false }) {
    const allStrikes =
        strikes ?? [...new Set(chain.map((row) => Number(row.strike)))].sort((a, b) => a - b);
    const getOption = (strike, type) =>
        chain.find((row) => Number(row.strike) === strike && row.option_type === type);

    return (
        <div className="max-h-[68vh] overflow-auto">
            <table className="min-w-[1180px] w-full border-collapse text-xs">
                <thead className="sticky top-0 z-10 bg-dark-900/95 backdrop-blur">
                    <tr className="border-b border-dark-700">
                        <th
                            className="bg-emerald-950/35 px-2 py-2 text-center font-semibold text-emerald-300"
                            colSpan={showGreeks ? 8 : 4}
                        >
                            CALLS (CE)
                        </th>
                        <th className="bg-dark-800 px-3 py-2 text-center text-dark-300">STRIKE</th>
                        <th
                            className="bg-rose-950/30 px-2 py-2 text-center font-semibold text-rose-300"
                            colSpan={showGreeks ? 8 : 4}
                        >
                            PUTS (PE)
                        </th>
                    </tr>
                    <tr className="border-b border-dark-700 text-dark-400">
                        {(showGreeks
                            ? ["OI", "Volume", "LTP", "IV", "Delta", "Gamma", "Theta", "Vega"]
                            : ["OI", "Volume", "LTP", "IV"]
                        ).map((label) => (
                            <th key={`ce-${label}`} className="px-2 py-2 text-right font-medium">
                                {label}
                            </th>
                        ))}
                        <th className="bg-dark-800 px-3 py-2 text-center font-medium">Strike</th>
                        {(showGreeks
                            ? ["OI", "Volume", "LTP", "IV", "Delta", "Gamma", "Theta", "Vega"]
                            : ["OI", "Volume", "LTP", "IV"]
                        ).map((label) => (
                            <th key={`pe-${label}`} className="px-2 py-2 text-right font-medium">
                                {label}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {allStrikes.map((strike) => {
                        const isAtm =
                            atmStrike !== null &&
                            atmStrike !== undefined &&
                            Number(strike) === Number(atmStrike);
                        return (
                            <tr
                                key={strike}
                                className={`border-b border-dark-800/70 hover:bg-dark-800/45 ${isAtm ? "bg-fuchsia-950/35" : ""}`}
                            >
                                <OptionCells
                                    option={getOption(strike, "CE")}
                                    side="call"
                                    showGreeks={showGreeks}
                                />
                                <td
                                    className={`bg-dark-800 px-3 py-2 text-center font-mono font-bold ${isAtm ? "text-fuchsia-200" : "text-dark-100"}`}
                                >
                                    {formatNumber(strike, 0)}
                                    {isAtm && (
                                        <span className="ml-1 text-[10px] font-medium text-fuchsia-300">
                                            ATM
                                        </span>
                                    )}
                                </td>
                                <OptionCells
                                    option={getOption(strike, "PE")}
                                    side="put"
                                    showGreeks={showGreeks}
                                />
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
