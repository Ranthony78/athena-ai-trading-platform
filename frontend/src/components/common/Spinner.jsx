import { Loader2 } from "lucide-react";

export default function Spinner({ size = "md", text = "" }) {
    const sizes = {
        sm: "w-4 h-4",
        md: "w-6 h-6",
        lg: "w-8 h-8",
    };

    return (
        <div className="flex flex-col items-center justify-center gap-3 p-8">
            <Loader2 className={`${sizes[size]} text-primary-500 animate-spin`} />
            {text && <p className="text-sm text-dark-400">{text}</p>}
        </div>
    );
}