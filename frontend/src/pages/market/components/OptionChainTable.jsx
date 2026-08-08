import { formatNumber, abbreviateNumber } from "../../../utils/formatters";

export default function OptionChainTable({ chain = [] }) {
    const strikes = [...new Set(chain.map((c) => c.strike))].sort(
        (a, b) => a - b
    );

    const getOption = (strike, type) =>
        chain.find(
            (c) => c.strike === strike && c.option_type === type
        );

    return (
        <div className="overflow-x-auto">
            <table className="table text-xs">
                <thead>
                    <tr>
                        <th className="text-green-400 text-center" colSpan={3}>
                            CALLS (CE)
                        </th>
                        <th className="text-center bg-dark-800 text-dark-300">
                            Strike
                        </th>
                        <th className="text-red-400 text-center" colSpan={3}>
                            PUTS (PE)
                        </th>
                    </tr>
                    <tr>
                        <th>OI</th>
                        <th>Volume</th>
                        <th>LTP</th>
                        <th className="bg-dark-800 text-center">—</th>
                        <th>LTP</th>
                        <th>Volume</th>
                        <th>OI</th>
                    </tr>
                </thead>
                <tbody>
                    {strikes.map((strike) => {
                        const ce = getOption(strike, "CE");
                        const pe = getOption(strike, "PE");

                        return (
                            <tr key={strike}>
                                <td className="text-green-400/70">
                                    {ce ? abbreviateNumber(ce.oi) : "—"}
                                </td>
                                <td className="text-green-400/50">
                                    {ce ? abbreviateNumber(ce.volume) : "—"}
                                </td>
                                <td className="text-green-400 font-mono font-semibold">
                                    {ce ? formatNumber(ce.ltp) : "—"}
                                </td>
                                <td className="bg-dark-800 text-center font-mono
                               font-bold text-dark-200">
                                    {formatNumber(strike)}
                                </td>
                                <td className="text-red-400 font-mono font-semibold">
                                    {pe ? formatNumber(pe.ltp) : "—"}
                                </td>
                                <td className="text-red-400/50">
                                    {pe ? abbreviateNumber(pe.volume) : "—"}
                                </td>
                                <td className="text-red-400/70">
                                    {pe ? abbreviateNumber(pe.oi) : "—"}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}