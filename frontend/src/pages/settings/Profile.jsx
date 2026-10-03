import { useState, useEffect, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Alert, Button, Card, Input, Select, Spinner } from "../../components/common";
import { authAPI } from "../../api/auth";
import useAuthStore from "../../store/authStore";

const EDITABLE = ["first_name", "last_name", "phone", "timezone"];

// The API answers a rejected field with { field: ["message", ...] }.
function fieldErrors(error) {
    const data = error?.response?.data;
    if (!data || typeof data !== "object") return {};
    return Object.fromEntries(
        Object.entries(data)
            .filter(([, messages]) => Array.isArray(messages))
            .map(([field, messages]) => [field, messages[0]])
    );
}

function generalError(error) {
    if (Object.keys(fieldErrors(error)).length) return null;
    return error?.response?.data?.message || "Could not save your profile. Please try again.";
}

export default function Profile() {
    const queryClient = useQueryClient();
    const setUser = useAuthStore((state) => state.setUser);
    const [form, setForm] = useState({
        first_name: "",
        last_name: "",
        phone: "",
        timezone: "Asia/Kolkata",
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
                phone: profile.phone || "",
                timezone: profile.timezone || "Asia/Kolkata",
            });
        }
    }, [profile]);

    const saveMutation = useMutation({
        mutationFn: (values) => authAPI.updateProfile(values),
        onSuccess: (response) => {
            // Keep the signed-in user (shown in the top bar) in step with the server.
            setUser(response.data.user);
            queryClient.invalidateQueries({ queryKey: ["profile"] });
        },
    });

    // Every IANA timezone the browser knows, plus the saved one if it is not in the list.
    const timezoneOptions = useMemo(() => {
        const known =
            typeof Intl.supportedValuesOf === "function" ? Intl.supportedValuesOf("timeZone") : [];
        const zones = new Set([...known, form.timezone].filter(Boolean));
        return [...zones].sort().map((zone) => ({ value: zone, label: zone }));
    }, [form.timezone]);

    const isDirty = profile
        ? EDITABLE.some((field) => form[field] !== (profile[field] || ""))
        : false;
    const errors = fieldErrors(saveMutation.error);

    const change = (field) => (event) => {
        saveMutation.reset();
        setForm((current) => ({ ...current, [field]: event.target.value }));
    };

    const handleSubmit = (event) => {
        event.preventDefault();
        saveMutation.mutate(Object.fromEntries(EDITABLE.map((field) => [field, form[field]])));
    };

    if (isLoading) return <Spinner />;

    return (
        <PageWrapper title="Profile" subtitle="Your account details">
            <Card title="Personal Information" className="max-w-lg">
                <form onSubmit={handleSubmit} className="space-y-4">
                    {saveMutation.isSuccess && (
                        <Alert type="success" message="Your profile has been updated." />
                    )}
                    {saveMutation.isError && generalError(saveMutation.error) && (
                        <Alert type="error" message={generalError(saveMutation.error)} />
                    )}
                    <div className="grid grid-cols-2 gap-4">
                        <Input
                            label="First Name"
                            value={form.first_name}
                            onChange={change("first_name")}
                            error={errors.first_name}
                            maxLength={150}
                        />
                        <Input
                            label="Last Name"
                            value={form.last_name}
                            onChange={change("last_name")}
                            error={errors.last_name}
                            maxLength={150}
                        />
                    </div>
                    <div>
                        <Input label="Email" type="email" value={profile?.email || ""} disabled />
                        <p className="mt-1 text-xs text-dark-500">
                            Email can&apos;t be changed here. Ask an administrator if it needs to
                            change.
                        </p>
                    </div>
                    <Input
                        label="Phone"
                        value={form.phone}
                        onChange={change("phone")}
                        error={errors.phone}
                        maxLength={20}
                    />
                    <Select
                        label="Timezone"
                        value={form.timezone}
                        onChange={change("timezone")}
                        options={timezoneOptions}
                        error={errors.timezone}
                    />
                    <div className="flex items-center justify-between pt-2">
                        <p className="text-xs text-dark-500">
                            Username: <span className="text-dark-300">{profile?.username}</span>
                        </p>
                        <Button
                            type="submit"
                            icon={Save}
                            loading={saveMutation.isPending}
                            disabled={!isDirty}
                        >
                            Save changes
                        </Button>
                    </div>
                </form>
            </Card>
        </PageWrapper>
    );
}
