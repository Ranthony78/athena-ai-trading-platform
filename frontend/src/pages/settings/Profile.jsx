import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { PageWrapper } from "../../components/layout";
import { Card, Input, Button, Spinner } from "../../components/common";
import { authAPI } from "../../api/auth";
import useAuthStore from "../../store/authStore";

export default function Profile() {
    const { setUser } = useAuthStore();
    const [form, setForm] = useState({
        first_name: "", last_name: "", email: "", phone: "", timezone: "",
    });

    const { data: profile, isLoading } = useQuery({
        queryKey: ["profile"],
        queryFn: () => authAPI.profile(),
        select: (res) => res.data.user,
    });

    useEffect(() => {
        if (profile) {
            setForm({
                first_name: profile.first_name || "",
                last_name: profile.last_name || "",
                email: profile.email || "",
                phone: profile.phone || "",
                timezone: profile.timezone || "Asia/Kolkata",
            });
        }
    }, [profile]);

    if (isLoading) return <Spinner />;

    return (
        <PageWrapper title="Profile" subtitle="Your account details">
            <Card title="Personal Information" className="max-w-lg">
                <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <Input label="First Name" value={form.first_name}
                            onChange={(e) => setForm(f => ({ ...f, first_name: e.target.value }))} />
                        <Input label="Last Name" value={form.last_name}
                            onChange={(e) => setForm(f => ({ ...f, last_name: e.target.value }))} />
                    </div>
                    <Input label="Email" type="email" value={form.email}
                        onChange={(e) => setForm(f => ({ ...f, email: e.target.value }))} />
                    <Input label="Phone" value={form.phone}
                        onChange={(e) => setForm(f => ({ ...f, phone: e.target.value }))} />
                    <Input label="Timezone" value={form.timezone}
                        onChange={(e) => setForm(f => ({ ...f, timezone: e.target.value }))} />
                    <div className="pt-2">
                        <p className="text-xs text-dark-500">
                            Username: <span className="text-dark-300">{profile?.username}</span>
                        </p>
                    </div>
                </div>
            </Card>
        </PageWrapper>
    );
}