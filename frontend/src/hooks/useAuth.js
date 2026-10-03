import { useMutation, useQuery } from "@tanstack/react-query";
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

function useAuthenticate(mutationFn) {
    const { login } = useAuthStore();
    const navigate = useNavigate();

    return useMutation({
        mutationFn,
        onSuccess: (response) => {
            // When registration needs approval the account exists but no
            // tokens are issued, so there is nothing to sign in with yet.
            if (response.data?.pending_approval) return;
            login(response.data);
            navigate("/dashboard");
        },
    });
}

// "open" | "approval" | "closed" - lets the sign-in page match the server's policy.
export function useRegistrationMode() {
    return useQuery({
        queryKey: ["registration-mode"],
        queryFn: () => authAPI.getRegistrationMode(),
        select: (response) => response.data.mode,
        staleTime: 5 * 60 * 1000,
        retry: false,
    });
}

export function useRegister() {
    return useAuthenticate((details) => authAPI.register(details));
}

export function useGoogleLogin() {
    return useAuthenticate((credential) => authAPI.googleLogin(credential));
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
