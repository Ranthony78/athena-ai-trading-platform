import { PageWrapper } from "../../components/layout";
import { Card } from "../../components/common";
import { User, Bell, Link2, Shield } from "lucide-react";

const settingsLinks = [
    {
        href: "/settings/profile",
        icon: User,
        title: "Profile",
        description: "Update your name, email, and timezone",
    },
    {
        href: "/notifications/preferences",
        icon: Bell,
        title: "Notifications",
        description: "Manage email and Telegram notifications",
    },
    {
        href: "/zerodha",
        icon: Link2,
        title: "Zerodha Connection",
        description: "Connect or manage your Kite account",
    },
];

export default function Settings() {
    return (
        <PageWrapper title="Settings" subtitle="Manage your account and preferences">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {settingsLinks.map((link) => (
                    <a key={link.href} href={link.href}>
                        <Card className="hover:border-primary-500 cursor-pointer
                             transition-colors">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-xl bg-primary-900/30
                                border border-primary-800 flex items-center
                                justify-center shrink-0">
                                    <link.icon className="w-5 h-5 text-primary-400" />
                                </div>
                                <div>
                                    <p className="text-sm font-semibold text-dark-100">
                                        {link.title}
                                    </p>
                                    <p className="text-xs text-dark-500 mt-0.5">
                                        {link.description}
                                    </p>
                                </div>
                            </div>
                        </Card>
                    </a>
                ))}
            </div>
        </PageWrapper>
    );
}