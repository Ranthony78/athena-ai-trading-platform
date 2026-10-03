import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowRight, LockKeyhole, ShieldCheck } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { AuthLayout } from "../../components/layout";
import { Alert, Button } from "../../components/common";
import { authAPI } from "../../api/auth";

export default function ResetPassword() {
    const [searchParams] = useSearchParams();
    const [password, setPassword] = useState("");
    const [passwordConfirm, setPasswordConfirm] = useState("");
    const uid = searchParams.get("uid") || "";
    const token = searchParams.get("token") || "";
    const mutation = useMutation({ mutationFn: (data) => authAPI.confirmPasswordReset(data) });
    const errorMessage =
        mutation.error?.response?.data?.message ||
        Object.values(mutation.error?.response?.data || {})
            .flat()
            .find((value) => typeof value === "string") ||
        "This reset link may be invalid or expired. Ask your administrator for a new link.";

    const handleSubmit = (event) => {
        event.preventDefault();
        mutation.mutate({ uid, token, new_password: password, password_confirm: passwordConfirm });
    };

    return (
        <AuthLayout>
            <div className="mb-8">
                <p className="auth-eyebrow mb-3 text-[11px] font-bold uppercase tracking-[0.2em]">
                    Account security
                </p>
                <h2 className="font-serif text-4xl font-medium tracking-tight text-dark-50">
                    Set a new password.
                </h2>
                <p className="mt-2 text-sm leading-6 text-dark-500">
                    Choose a new password for your Athena account.
                </p>
            </div>

            {mutation.error && (
                <div className="mb-5">
                    <Alert type="error" message={errorMessage} />
                </div>
            )}
            {mutation.isSuccess ? (
                <div className="space-y-5">
                    <Alert
                        type="success"
                        message={
                            mutation.data?.data?.message || "Password updated. You can now sign in."
                        }
                    />
                    <Link
                        to="/login"
                        className="auth-signin-button flex h-12 w-full items-center justify-center gap-2 rounded-xl text-sm font-semibold text-white"
                    >
                        Go to sign in <ArrowRight className="h-4 w-4" />
                    </Link>
                </div>
            ) : !uid || !token ? (
                <div className="space-y-5">
                    <Alert
                        type="error"
                        message="This password reset link is incomplete. Ask your administrator for a new one."
                    />
                    <Link
                        to="/login"
                        className="auth-accent-text text-sm font-semibold hover:underline"
                    >
                        Back to sign in
                    </Link>
                </div>
            ) : (
                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label
                            htmlFor="new-password"
                            className="mb-2 block text-xs font-semibold text-dark-300"
                        >
                            New password
                        </label>
                        <div className="relative">
                            <LockKeyhole
                                className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-500"
                                aria-hidden="true"
                            />
                            <input
                                id="new-password"
                                type="password"
                                autoComplete="new-password"
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                required
                                minLength={8}
                                className="auth-input h-12 w-full rounded-xl border border-dark-700 bg-dark-900 pl-10 pr-4 text-sm text-dark-100 outline-none placeholder:text-dark-500 hover:border-dark-600"
                            />
                        </div>
                    </div>
                    <div>
                        <label
                            htmlFor="confirm-password"
                            className="mb-2 block text-xs font-semibold text-dark-300"
                        >
                            Confirm new password
                        </label>
                        <input
                            id="confirm-password"
                            type="password"
                            autoComplete="new-password"
                            value={passwordConfirm}
                            onChange={(event) => setPasswordConfirm(event.target.value)}
                            required
                            minLength={8}
                            className="auth-input h-12 w-full rounded-xl border border-dark-700 bg-dark-900 px-4 text-sm text-dark-100 outline-none placeholder:text-dark-500 hover:border-dark-600"
                        />
                    </div>
                    <Button
                        type="submit"
                        variant="primary"
                        loading={mutation.isPending}
                        className="auth-signin-button h-12 w-full rounded-xl text-sm font-semibold text-white"
                    >
                        Update password{" "}
                        {!mutation.isPending && (
                            <ArrowRight className="ml-1 h-4 w-4" aria-hidden="true" />
                        )}
                    </Button>
                </form>
            )}

            <div className="mt-6 flex items-center justify-center gap-2 text-xs text-dark-500">
                <ShieldCheck className="auth-accent-text h-4 w-4" aria-hidden="true" />
                Secure password reset
            </div>
        </AuthLayout>
    );
}
