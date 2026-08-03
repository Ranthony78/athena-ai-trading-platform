export default function Card({
    title,
    subtitle,
    actions,
    children,
    className = "",
    padding = true,
}) {
    return (
        <div className={`card ${padding ? "" : "p-0"} ${className}`}>
            {(title || actions) && (
                <div className="card-header">
                    <div>
                        {title && <h3 className="card-title">{title}</h3>}
                        {subtitle && (
                            <p className="text-xs text-dark-500 mt-0.5">{subtitle}</p>
                        )}
                    </div>
                    {actions && (
                        <div className="flex items-center gap-2">{actions}</div>
                    )}
                </div>
            )}
            {children}
        </div>
    );
}