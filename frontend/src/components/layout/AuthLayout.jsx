import { Activity } from "lucide-react";
import { APP_NAME } from "../../utils/constants";

function MarketIllustration() {
    return (
        <svg
            viewBox="0 0 560 220"
            role="img"
            aria-label="Decorative chart showing a rising market trend"
            className="h-auto w-full max-w-xl"
        >
            <defs>
                <linearGradient id="auth-chart-fill" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#e9a0bc" stopOpacity=".24" />
                    <stop offset="100%" stopColor="#e9a0bc" stopOpacity="0" />
                </linearGradient>
            </defs>
            {[38, 82, 126, 170].map((y) => (
                <line key={y} x1="12" x2="548" y1={y} y2={y} stroke="#ffffff" strokeOpacity=".1" />
            ))}
            <path
                d="M24 166 C82 156 91 137 143 142 S215 120 259 128 S327 102 369 111 S437 72 482 81 S523 56 540 48 L540 190 L24 190Z"
                fill="url(#auth-chart-fill)"
            />
            <path
                d="M24 166 C82 156 91 137 143 142 S215 120 259 128 S327 102 369 111 S437 72 482 81 S523 56 540 48"
                fill="none"
                stroke="#f2c1d3"
                strokeWidth="3"
                strokeLinecap="round"
            />
            {[
                { x: 98, y: 130, h: 33, color: "#22c55e" },
                { x: 181, y: 127, h: 28, color: "#ef4444" },
                { x: 265, y: 108, h: 37, color: "#22c55e" },
                { x: 350, y: 91, h: 33, color: "#22c55e" },
                { x: 437, y: 63, h: 39, color: "#22c55e" },
                { x: 506, y: 42, h: 34, color: "#22c55e" },
            ].map((candle) => (
                <g key={candle.x}>
                    <line
                        x1={candle.x + 8}
                        x2={candle.x + 8}
                        y1={candle.y - 12}
                        y2={candle.y + candle.h + 10}
                        stroke={candle.color}
                        strokeWidth="2"
                    />
                    <rect
                        x={candle.x}
                        y={candle.y}
                        width="16"
                        height={candle.h}
                        rx="1"
                        fill={candle.color}
                    />
                </g>
            ))}
            <circle cx="540" cy="48" r="5" fill="#f2c1d3" />
        </svg>
    );
}

export default function AuthLayout({ children }) {
    return (
        <main className="auth-shell min-h-screen p-3 font-sans sm:p-6 lg:p-8">
            <div className="auth-surface mx-auto grid min-h-[min(760px,calc(100vh-3rem))] w-full max-w-6xl grid-cols-1 overflow-hidden rounded-[28px] border lg:grid-cols-[1.12fr_0.88fr]">
                <section
                    className="auth-brand-panel relative flex min-h-[310px] flex-col overflow-hidden px-7 py-7 text-white sm:px-10 sm:py-9 lg:min-h-[680px] lg:px-12 lg:py-10"
                    aria-label="Athena introduction"
                >
                    <div className="pointer-events-none absolute -right-28 -top-32 h-80 w-80 rounded-full bg-rose-400/15 blur-3xl" />
                    <div className="pointer-events-none absolute -bottom-36 -left-24 h-80 w-80 rounded-full bg-amber-500/10 blur-3xl" />
                    <div className="relative flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/15 bg-white/10">
                            <Activity className="h-5 w-5 text-rose-200" aria-hidden="true" />
                        </div>
                        <div>
                            <p className="text-base font-bold tracking-tight">{APP_NAME}</p>
                            <p className="text-[11px] text-rose-100/65">AI Trading Platform</p>
                        </div>
                    </div>

                    <div className="relative mt-8 max-w-lg lg:mt-16">
                        <div className="mb-4 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-rose-100/80">
                            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_14px_rgba(52,211,153,0.8)]" />
                            Options intelligence for a brighter tomorrow
                        </div>
                        <h1 className="max-w-lg font-serif text-3xl font-medium leading-[1.08] tracking-tight sm:text-4xl lg:text-[42px]">
                            Read the move before it happens.
                        </h1>
                        <p className="mt-4 max-w-md text-sm leading-6 text-rose-100/75 sm:text-base">
                            Market context, options insights, and a clearer view of risk in one
                            focused workspace.
                        </p>
                        <div className="mt-5 flex flex-wrap gap-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-rose-50/85">
                            {["Market data", "Options analytics", "Risk scenarios"].map(
                                (feature) => (
                                    <span
                                        key={feature}
                                        className="rounded-full border border-rose-100/15 bg-white/[0.06] px-3 py-1.5"
                                    >
                                        {feature}
                                    </span>
                                )
                            )}
                        </div>
                    </div>

                    <div className="relative mt-auto hidden pt-10 lg:block">
                        <MarketIllustration />
                    </div>
                    <p className="relative mt-8 text-xs tracking-wide text-rose-100/55 lg:mt-5">
                        Markets reveal more to prepared minds.
                    </p>
                </section>

                <section
                    className="flex items-center justify-center px-6 py-10 sm:px-10 lg:px-11"
                    aria-label="Sign in"
                >
                    <div className="w-full max-w-md">{children}</div>
                </section>
            </div>
        </main>
    );
}
