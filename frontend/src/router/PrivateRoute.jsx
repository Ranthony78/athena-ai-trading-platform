import { Navigate, Outlet } from "react-router-dom";
import useAuthStore from "../store/authStore";
import { Sidebar } from "../components/layout";
import { Topbar } from "../components/layout";

export default function PrivateRoute() {
    const { isAuthenticated } = useAuthStore();

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return (
        <div className="flex h-screen bg-dark-950 overflow-hidden">
            <Sidebar />
            <div className="flex flex-col flex-1 overflow-hidden">
                <Topbar />
                <main className="flex-1 overflow-y-auto p-6">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}