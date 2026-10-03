import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ArrowRight, Eye, EyeOff, LockKeyhole, ShieldCheck, UserRound, Mail } from "lucide-react";
import { AuthLayout } from "../../components/layout";
import { Alert, Button } from "../../components/common";
import { useGoogleLogin, useLogin, useRegister, useRegistrationMode } from "../../hooks/useAuth";

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function errorMessage(error) {
    const data = error?.response?.data;
    if (data?.message) return data.message;
    if (data && typeof data === "object") {
        const message = Object.values(data)
            .flat()
            .find((value) => typeof value === "string");
        if (message) return message;
    }
    return "Something went wrong. Please try again.";
}

export default function Login() {
    const isSignup = useLocation().pathname === "/signup";
    const [form, setForm] = useState({
        username: "",
        email: "",
        first_name: "",
        last_name: "",
        password: "",
        password_confirm: "",
    });
    const [showPassword, setShowPassword] = useState(false);
    const googleButton = useRef(null);
    const loginMutation = useLogin();
    const registerMutation = useRegister();
    const googleMutation = useGoogleLogin();
    const googleSignIn = googleMutation.mutate;
    const activeMutation = isSignup ? registerMutation : loginMutation;
    const registrationMode = useRegistrationMode().data;
    const isClosed = registrationMode === "closed";
    const needsApproval = registrationMode === "approval";
    // Set when a sign-up (password or first Google sign-in) was accepted but
    // an administrator still has to approve it.
    const pendingMessage = [registerMutation.data, googleMutation.data]
        .map((response) => response?.data)
        .find((data) => data?.pending_approval)?.message;

    useEffect(() => {
        if (!googleClientId || !googleButton.current) return undefined;
        let cancelled = false;
        const renderButton = () => {
            if (cancelled || !window.google?.accounts?.id || !googleButton.current) return;
            window.google.accounts.id.initialize({
                client_id: googleClientId,
                callback: ({ credential }) => googleSignIn(credential),
            });
            window.google.accounts.id.renderButton(googleButton.current, {
                theme: "filled_black",
                size: "large",
                shape: "rectangular",
                text: isSignup ? "signup_with" : "signin_with",
                width: 360,
            });
        };

        if (window.google?.accounts?.id) {
            renderButton();
        } else {
            const script = document.createElement("script");
            script.src = "https://accounts.google.com/gsi/client";
            script.async = true;
            script.defer = true;
            script.onload = renderButton;
            document.head.appendChild(script);
        }
        return () => {
            cancelled = true;
        };
    }, [isSignup, googleSignIn]);

    const handleSubmit = (event) => {
        event.preventDefault();
        if (isSignup) {
            registerMutation.mutate(form);
        } else {
            loginMutation.mutate({ username: form.username, password: form.password });
        }
    };

    const setField = (event) =>
        setForm((current) => ({ ...current, [event.target.name]: event.target.value }));

    // No form to show: either the request is waiting for approval, or nobody
    // can register right now.
    if (pendingMessage || (isSignup && isClosed)) {
        return (
            <AuthLayout>
                <div className="mb-8">
                    <p className="auth-eyebrow mb-3 text-[11px] font-bold uppercase tracking-[0.2em]">
                        {pendingMessage ? "Request received" : "Registration closed"}
                    </p>
                    <h2 className="font-serif text-4xl font-medium tracking-tight text-dark-50">
                        {pendingMessage ? "Almost there." : "Sign-up is closed."}
                    </h2>
                </div>
                <div className="mb-6">
                    {pendingMessage ? (
                        <Alert type="success" message={pendingMessage} />
                    ) : (
                        <Alert
                            type="warning"
                            message="Registration is closed. Ask an administrator to create an account for you."
                        />
                    )}
                </div>
                <Link
                    to="/login"
                    className="auth-accent-text text-sm font-semibold hover:underline"
                >
                    Back to sign in
                </Link>
            </AuthLayout>
        );
    }

    return (
        <AuthLayout>
            <div className="mb-8">
                <p className="auth-eyebrow mb-3 text-[11px] font-bold uppercase tracking-[0.2em]">
                    {isSignup ? "Create your account" : "Sign in to your account"}
                </p>
                <h2 className="font-serif text-4xl font-medium tracking-tight text-dark-50">
                    {isSignup ? "Start with Athena." : "Welcome back."}
                </h2>
                <p className="mt-2 text-sm leading-6 text-dark-500">
                    {isSignup
                        ? "Create a secure account for your trading workspace."
                        : "Sign in securely to your Athena trading workspace."}
                </p>
            </div>

            {isSignup && needsApproval && (
                <div className="mb-5">
                    <Alert
                        type="info"
                        message="New accounts need administrator approval before you can sign in."
                    />
                </div>
            )}
            {activeMutation.error && (
                <div className="mb-5">
                    <Alert type="error" message={errorMessage(activeMutation.error)} />
                </div>
            )}
            {googleMutation.error && (
                <div className="mb-5">
                    <Alert type="error" message={errorMessage(googleMutation.error)} />
                </div>
            )}

            {googleClientId && (
                <div className="mb-5">
                    <div ref={googleButton} className="flex min-h-10 justify-center" />
                    <div className="my-5 flex items-center gap-3 text-[11px] uppercase tracking-widest text-dark-500">
                        <span className="h-px flex-1 bg-dark-700" />
                        or continue with email
                        <span className="h-px flex-1 bg-dark-700" />
                    </div>
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
                {isSignup && (
                    <>
                        <div className="grid grid-cols-2 gap-3">
                            {[
                                ["first_name", "First name"],
                                ["last_name", "Last name"],
                            ].map(([name, label]) => (
                                <div key={name}>
                                    <label
                                        htmlFor={name}
                                        className="mb-2 block text-xs font-semibold text-dark-300"
                                    >
                                        {label}
                                    </label>
                                    <input
                                        id={name}
                                        name={name}
                                        autoComplete={name}
                                        value={form[name]}
                                        onChange={setField}
                                        className="auth-input h-12 w-full rounded-xl border border-dark-700 bg-dark-900 px-4 text-sm text-dark-100 outline-none placeholder:text-dark-500 hover:border-dark-600"
                                    />
                                </div>
                            ))}
                        </div>
                        <div>
                            <label
                                htmlFor="email"
                                className="mb-2 block text-xs font-semibold text-dark-300"
                            >
                                Email
                            </label>
                            <div className="relative">
                                <Mail
                                    className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-500"
                                    aria-hidden="true"
                                />
                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    autoComplete="email"
                                    placeholder="you@example.com"
                                    value={form.email}
                                    onChange={setField}
                                    className="auth-input h-12 w-full rounded-xl border border-dark-700 bg-dark-900 pl-10 pr-4 text-sm text-dark-100 outline-none placeholder:text-dark-500 hover:border-dark-600"
                                    required
                                />
                            </div>
                        </div>
                    </>
                )}
                <div>
                    <label
                        htmlFor="username"
                        className="mb-2 block text-xs font-semibold text-dark-300"
                    >
                        Username
                    </label>
                    <div className="relative">
                        <UserRound
                            className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-500"
                            aria-hidden="true"
                        />
                        <input
                            id="username"
                            name="username"
                            type="text"
                            autoComplete="username"
                            placeholder="Enter your username"
                            value={form.username}
                            onChange={setField}
                            className="auth-input h-12 w-full rounded-xl border border-dark-700 bg-dark-900 pl-10 pr-4 text-sm text-dark-100 outline-none placeholder:text-dark-500 hover:border-dark-600"
                            required
                        />
                    </div>
                </div>
                <div>
                    <label
                        htmlFor="password"
                        className="mb-2 block text-xs font-semibold text-dark-300"
                    >
                        Password
                    </label>
                    <div className="relative">
                        <LockKeyhole
                            className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-500"
                            aria-hidden="true"
                        />
                        <input
                            id="password"
                            name="password"
                            type={showPassword ? "text" : "password"}
                            autoComplete={isSignup ? "new-password" : "current-password"}
                            placeholder={isSignup ? "Create a password" : "Enter your password"}
                            value={form.password}
                            onChange={setField}
                            className="auth-input h-12 w-full rounded-xl border border-dark-700 bg-dark-900 pl-10 pr-12 text-sm text-dark-100 outline-none placeholder:text-dark-500 hover:border-dark-600"
                            required
                            minLength={8}
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword((visible) => !visible)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-1 text-dark-500 transition hover:text-dark-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                            aria-label={showPassword ? "Hide password" : "Show password"}
                            aria-pressed={showPassword}
                        >
                            {showPassword ? (
                                <EyeOff className="h-4 w-4" />
                            ) : (
                                <Eye className="h-4 w-4" />
                            )}
                        </button>
                    </div>
                    {!isSignup && (
                        <p className="mt-2 text-right text-xs text-dark-500">
                            Forgot your password? Contact your administrator.
                        </p>
                    )}
                </div>
                {isSignup && (
                    <div>
                        <label
                            htmlFor="password_confirm"
                            className="mb-2 block text-xs font-semibold text-dark-300"
                        >
                            Confirm password
                        </label>
                        <input
                            id="password_confirm"
                            name="password_confirm"
                            type="password"
                            autoComplete="new-password"
                            placeholder="Enter your password again"
                            value={form.password_confirm}
                            onChange={setField}
                            className="auth-input h-12 w-full rounded-xl border border-dark-700 bg-dark-900 px-4 text-sm text-dark-100 outline-none placeholder:text-dark-500 hover:border-dark-600"
                            required
                        />
                    </div>
                )}
                <Button
                    type="submit"
                    variant="primary"
                    loading={activeMutation.isPending || googleMutation.isPending}
                    className="auth-signin-button !mt-7 h-12 w-full rounded-xl text-sm font-semibold text-white transition"
                >
                    {isSignup ? "Create account" : "Sign in"}
                    {!activeMutation.isPending && (
                        <ArrowRight className="ml-1 h-4 w-4" aria-hidden="true" />
                    )}
                </Button>
            </form>

            {!isClosed && (
                <p className="mt-6 text-center text-sm text-dark-500">
                    {isSignup ? "Already have an account? " : "New to Athena? "}
                    <Link
                        to={isSignup ? "/login" : "/signup"}
                        className="auth-accent-text font-semibold hover:underline"
                    >
                        {isSignup ? "Sign in" : "Create an account"}
                    </Link>
                </p>
            )}
            <div className="mt-5 flex items-center justify-center gap-2 text-xs text-dark-500">
                <ShieldCheck className="auth-accent-text h-4 w-4" aria-hidden="true" />
                Secure access to your Athena account
            </div>
        </AuthLayout>
    );
}
