import { Loader2 } from "lucide-react";

export default function Button({
    children,
    variant = "primary",
    size = "md",
    loading = false,
    disabled = false,
    icon: Icon = null,
    onClick,
    type = "button",
    className = "",
}) {
    const variants = {
        primary: "btn-primary",
        secondary: "btn-secondary",
        danger: "btn-danger",
        success: "btn-success",
        ghost: "btn-ghost",
    };

    const sizes = {
        sm: "btn-sm",
        md: "",
        lg: "btn-lg",
    };

    return (
        <button
            type={type}
            onClick={onClick}
            disabled={disabled || loading}
            className={`${variants[variant]} ${sizes[size]} ${className}`}
        >
            {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
            ) : Icon ? (
                <Icon className="w-4 h-4" />
            ) : null}
            {children}
        </button>
    );
}