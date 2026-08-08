import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { authAPI } from "../api/auth";
import useAuthStore from "../store/authStore";

export function useLogin() {
    const { login } = useAuthStore();
    const navigate = useNavigate();

    return useMutation({
        mutationFn: (credentials) => authAPI.login(credentials),
        onSuccess: (response) => {
            login(response.data);
            navigate("/dashboard");
        },
    });
}

export function useLogout() {
    const { logout, refreshToken } = useAuthStore();
    const navigate = useNavigate();

    return useMutation({
        mutationFn: () => authAPI.logout(refreshToken),
        onSettled: () => {
            logout();
            navigate("/login");
        },
    });
}