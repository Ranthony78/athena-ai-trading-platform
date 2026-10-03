export default function PageWrapper({
    title,
    subtitle,
    actions,
    children,
    className = "",
    headerContent,
    headerClassName = "",
}) {
    return (
        <div className={`space-y-6 ${className}`}>
            {/* Page Header */}
            {(title || actions) && (
                <div className={headerClassName}>
                    <div className="flex flex-wrap gap-4 items-start justify-between">
                        <div>
                            {title && <h1 className="page-title">{title}</h1>}
                            {subtitle && <p className="page-subtitle">{subtitle}</p>}
                        </div>
                        {actions && <div className="flex items-center gap-2">{actions}</div>}
                    </div>
                    {headerContent}
                </div>
            )}

            {/* Content */}
            {children}
        </div>
    );
}
