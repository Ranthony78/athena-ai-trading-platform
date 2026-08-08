import Spinner from "./Spinner";
import EmptyState from "./EmptyState";

export default function Table({
    columns = [],
    data = [],
    loading = false,
    emptyTitle = "No data",
    emptyDescription = "",
}) {
    if (loading) return <Spinner text="Loading..." />;

    return (
        <div className="table-wrapper">
            <table className="table">
                <thead>
                    <tr>
                        {columns.map((col) => (
                            <th
                                key={col.key}
                                style={{ width: col.width }}
                                className={col.className || ""}
                            >
                                {col.label}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.length === 0 ? (
                        <tr>
                            <td colSpan={columns.length}>
                                <EmptyState
                                    title={emptyTitle}
                                    description={emptyDescription}
                                />
                            </td>
                        </tr>
                    ) : (
                        data.map((row, i) => (
                            <tr key={row.id || i}>
                                {columns.map((col) => (
                                    <td key={col.key} className={col.cellClassName || ""}>
                                        {col.render
                                            ? col.render(row[col.key], row)
                                            : row[col.key] ?? "—"}
                                    </td>
                                ))}
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
}