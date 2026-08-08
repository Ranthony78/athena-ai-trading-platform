export default function PageWrapper({ title, subtitle, actions, children }) {
    return (
        <div className="space-y-6">
            {/* Page Header */}
            {(title || actions) && (
                <div className="flex items-start justify-between">
                    <div>
                        {title && <h1 className="page-title">{title}</h1>}
                        {subtitle && <p className="page-subtitle">{subtitle}</p>}
                    </div>
                    {actions && (
                        <div className="flex items-center gap-2">
                            {actions}
                        </div>
                    )}
                </div>
            )}

            {/* Content */}
            {children}
        </div>
    );
}