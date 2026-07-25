import { X } from "lucide-react";
import { useEffect } from "react";

export default function Modal({
    isOpen,
    onClose,
    title,
    children,
    size = "md",
}) {
    const sizes = {
        sm: "max-w-md",
        md: "max-w-lg",
        lg: "max-w-2xl",
        xl: "max-w-4xl",
    };

    useEffect(() => {
        const handleEsc = (e) => {
            if (e.key === "Escape") onClose();
        };
        if (isOpen) document.addEventListener("keydown", handleEsc);
        return () => document.removeEventListener("keydown", handleEsc);
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Overlay */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className={`relative w-full ${sizes[size]} card z-10`}>
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-base font-semibold text-dark-100">{title}</h2>
                    <button
                        onClick={onClose}
                        className="p-1 rounded-lg text-dark-400 hover:text-dark-100
                       hover:bg-dark-800 transition-colors"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Content */}
                {children}
            </div>
        </div>
    );
}