import { AlertCircle, CheckCircle, Info, XCircle } from "lucide-react";

export default function Alert({ type = "info", title, message }) {
    const config = {
        info: {
            icon: Info,
            classes: "bg-blue-900/30 border-blue-800 text-blue-300",
            iconClass: "text-blue-400",
        },
        success: {
            icon: CheckCircle,
            classes: "bg-green-900/30 border-green-800 text-green-300",
            iconClass: "text-green-400",
        },
        warning: {
            icon: AlertCircle,
            classes: "bg-yellow-900/30 border-yellow-800 text-yellow-300",
            iconClass: "text-yellow-400",
        },
        error: {
            icon: XCircle,
            classes: "bg-red-900/30 border-red-800 text-red-300",
            iconClass: "text-red-400",
        },
    };

    const { icon: Icon, classes, iconClass } = config[type];

    return (
        <div className={`flex gap-3 p-3 rounded-lg border text-sm ${classes}`}>
            <Icon className={`w-4 h-4 shrink-0 mt-0.5 ${iconClass}`} />
            <div>
                {title && <p className="font-medium mb-0.5">{title}</p>}
                {message && <p className="opacity-80">{message}</p>}
            </div>
        </div>
    );
}