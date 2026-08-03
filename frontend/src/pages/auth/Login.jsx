import { useState } from "react";
import { AuthLayout } from "../../components/layout";
import { Button, Input, Alert } from "../../components/common";
import { useLogin } from "../../hooks/useAuth";

export default function Login() {
    const [form, setForm] = useState({ username: "", password: "" });
    const { mutate: login, isPending, error } = useLogin();

    const handleSubmit = (e) => {
        e.preventDefault();
        login(form);
    };

    return (
        <AuthLayout>
            <h2 className="text-lg font-semibold text-dark-100 mb-1">
                Welcome back
            </h2>
            <p className="text-sm text-dark-500 mb-6">
                Sign in to your trading account
            </p>

            {error && (
                <Alert
                    type="error"
                    message={
                        error.response?.data?.message || "Invalid credentials"
                    }
                    className="mb-4"
                />
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                    label="Username"
                    type="text"
                    placeholder="Enter your username"
                    value={form.username}
                    onChange={(e) =>
                        setForm((f) => ({ ...f, username: e.target.value }))
                    }
                    required
                />
                <Input
                    label="Password"
                    type="password"
                    placeholder="Enter your password"
                    value={form.password}
                    onChange={(e) =>
                        setForm((f) => ({ ...f, password: e.target.value }))
                    }
                    required
                />
                <Button
                    type="submit"
                    variant="primary"
                    loading={isPending}
                    className="w-full"
                >
                    Sign In
                </Button>
            </form>
        </AuthLayout>
    );
}