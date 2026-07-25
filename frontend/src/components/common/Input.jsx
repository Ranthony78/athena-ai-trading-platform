export default function Input({
    label,
    error,
    className = "",
    ...props
}) {
    return (
        <div className={className}>
            {label && <label className="label">{label}</label>}
            <input className={`input ${error ? "border-red-500" : ""}`} {...props} />
            {error && (
                <p className="text-xs text-red-400 mt-1">{error}</p>
            )}
        </div>
    );
}