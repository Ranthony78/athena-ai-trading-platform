export default function Select({
    label,
    options = [],
    error,
    className = "",
    ...props
}) {
    return (
        <div className={className}>
            {label && <label className="label">{label}</label>}
            <select
                className={`input ${error ? "border-red-500" : ""}`}
                {...props}
            >
                {options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                        {opt.label}
                    </option>
                ))}
            </select>
            {error && (
                <p className="text-xs text-red-400 mt-1">{error}</p>
            )}
        </div>
    );
}