import { Activity } from "lucide-react";
import { APP_NAME } from "../../utils/constants";

export default function AuthLayout({ children }) {
    return (
        <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="flex items-center justify-center gap-3 mb-8">
                    <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center
                          justify-center">
                        <Activity className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-dark-50">{APP_NAME}</h1>
                        <p className="text-xs text-dark-500">AI Trading Platform</p>
                    </div>
                </div>

                {/* Card */}
                <div className="card p-6">
                    {children}
                </div>
            </div>
        </div>
    );
}