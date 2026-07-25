import { Inbox } from "lucide-react";

export default function EmptyState({
    icon: Icon = Inbox,
    title = "No data found",
    description = "",
    action = null,
}) {
    return (
        <div className="flex flex-col items-center justify-center py-16
                    text-center">
            <div className="w-12 h-12 rounded-full bg-dark-800 flex items-center
                      justify-center mb-4">
                <Icon className="w-6 h-6 text-dark-500" />
            </div>
            <h3 className="text-sm font-medium text-dark-300 mb-1">{title}</h3>
            {description && (
                <p className="text-xs text-dark-500 max-w-xs">{description}</p>
            )}
            {action && <div className="mt-4">{action}</div>}
        </div>
    );
}