import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Mail, Search, ShieldCheck, UserRound, UserX } from "lucide-react";
import { authAPI } from "../../api/auth";
import { Alert, Badge, Button, Card, Spinner } from "../../components/common";
import { PageWrapper } from "../../components/layout";

function formatDate(value) {
    if (!value) return "Never";
    return new Date(value).toLocaleString();
}

function getErrorMessage(error) {
    return error?.response?.data?.message || "Could not load or update users. Please try again.";
}

export default function UserManagement() {
    const [search, setSearch] = useState("");
    const [page, setPage] = useState(1);
    const [resetNotice, setResetNotice] = useState("");
    const queryClient = useQueryClient();
    const usersQuery = useQuery({
        queryKey: ["managed-users", search, page],
        queryFn: () => authAPI.getUsers({ search, page }),
        retry: false,
    });
    const statusMutation = useMutation({
        mutationFn: ({ id, isActive }) => authAPI.setUserActive(id, isActive),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["managed-users"] }),
    });
    const passwordResetMutation = useMutation({
        mutationFn: (userId) => authAPI.sendUserPasswordReset(userId),
        onSuccess: (_response, userId) => {
            const target = users.find((user) => user.id === userId);
            setResetNotice(
                `Reset instructions were sent to ${target?.email || "the user's email"}.`
            );
        },
    });

    const users = usersQuery.data?.data?.results || [];
    const count = usersQuery.data?.data?.count || 0;
    const isForbidden = usersQuery.error?.response?.status === 403;

    return (
        <PageWrapper
            title="User Management"
            subtitle="Review accounts and control access to Athena"
        >
            {(usersQuery.error || statusMutation.error) && (
                <Alert
                    type="error"
                    message={
                        isForbidden
                            ? "Staff access is required to manage users."
                            : getErrorMessage(statusMutation.error || usersQuery.error)
                    }
                />
            )}
            {passwordResetMutation.error && (
                <Alert type="error" message={getErrorMessage(passwordResetMutation.error)} />
            )}
            {resetNotice && (
                <Alert
                    type="success"
                    message={`${resetNotice} In local development, the reset link is printed in the Django terminal.`}
                />
            )}

            <Card>
                <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <p className="text-sm font-semibold text-dark-100">Accounts</p>
                        <p className="mt-1 text-xs text-dark-500">
                            {count} registered {count === 1 ? "user" : "users"}
                        </p>
                    </div>
                    <label className="relative block w-full sm:max-w-xs">
                        <Search
                            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-500"
                            aria-hidden="true"
                        />
                        <input
                            type="search"
                            value={search}
                            onChange={(event) => {
                                setSearch(event.target.value);
                                setPage(1);
                            }}
                            placeholder="Search name, username, or email"
                            aria-label="Search users"
                            className="h-10 w-full rounded-lg border border-dark-700 bg-dark-900 pl-9 pr-3 text-sm text-dark-100 outline-none placeholder:text-dark-500 focus:border-primary-500"
                        />
                    </label>
                </div>

                {usersQuery.isLoading ? (
                    <Spinner text="Loading users..." />
                ) : isForbidden ? null : (
                    <>
                        <div className="overflow-x-auto">
                            <table className="w-full min-w-[760px] text-left text-sm">
                                <thead className="border-b border-dark-700 text-xs uppercase tracking-wide text-dark-500">
                                    <tr>
                                        <th className="px-3 py-3 font-semibold">User</th>
                                        <th className="px-3 py-3 font-semibold">Role</th>
                                        <th className="px-3 py-3 font-semibold">Status</th>
                                        <th className="px-3 py-3 font-semibold">Last sign in</th>
                                        <th className="px-3 py-3 text-right font-semibold">
                                            Actions
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-dark-800">
                                    {users.map((managedUser) => (
                                        <tr key={managedUser.id} className="text-dark-300">
                                            <td className="px-3 py-4">
                                                <div className="flex items-center gap-3">
                                                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-dark-800 text-dark-400">
                                                        <UserRound className="h-4 w-4" />
                                                    </span>
                                                    <div className="min-w-0">
                                                        <p className="truncate font-medium text-dark-100">
                                                            {managedUser.first_name ||
                                                            managedUser.last_name
                                                                ? `${managedUser.first_name} ${managedUser.last_name}`.trim()
                                                                : managedUser.username}
                                                        </p>
                                                        <p className="truncate text-xs text-dark-400">
                                                            @{managedUser.username}
                                                        </p>
                                                        <p className="truncate text-xs text-dark-500">
                                                            {managedUser.email || "No email"}
                                                        </p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-3 py-4">
                                                <span className="inline-flex items-center gap-1.5 text-xs">
                                                    {managedUser.is_staff && (
                                                        <ShieldCheck className="h-3.5 w-3.5 text-primary-400" />
                                                    )}
                                                    {managedUser.is_staff ? "Staff" : "User"}
                                                </span>
                                            </td>
                                            <td className="px-3 py-4">
                                                <Badge
                                                    variant={
                                                        managedUser.is_active ? "green" : "red"
                                                    }
                                                >
                                                    {managedUser.is_active ? "Active" : "Inactive"}
                                                </Badge>
                                            </td>
                                            <td className="px-3 py-4 text-xs text-dark-400">
                                                {formatDate(managedUser.last_login)}
                                            </td>
                                            <td className="px-3 py-4">
                                                <div className="flex justify-end gap-2">
                                                    <Button
                                                        size="sm"
                                                        variant="secondary"
                                                        loading={
                                                            passwordResetMutation.isPending &&
                                                            passwordResetMutation.variables ===
                                                                managedUser.id
                                                        }
                                                        disabled={
                                                            passwordResetMutation.isPending ||
                                                            !managedUser.email ||
                                                            !managedUser.is_active
                                                        }
                                                        onClick={() => {
                                                            setResetNotice("");
                                                            passwordResetMutation.mutate(
                                                                managedUser.id
                                                            );
                                                        }}
                                                        icon={Mail}
                                                        title={
                                                            !managedUser.email
                                                                ? "This user has no email address"
                                                                : !managedUser.is_active
                                                                  ? "Activate this account before resetting its password"
                                                                  : "Email a password reset link"
                                                        }
                                                    >
                                                        Send reset link
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        variant={
                                                            managedUser.is_active
                                                                ? "danger"
                                                                : "secondary"
                                                        }
                                                        loading={
                                                            statusMutation.isPending &&
                                                            statusMutation.variables?.id ===
                                                                managedUser.id
                                                        }
                                                        disabled={statusMutation.isPending}
                                                        onClick={() =>
                                                            statusMutation.mutate({
                                                                id: managedUser.id,
                                                                isActive: !managedUser.is_active,
                                                            })
                                                        }
                                                        icon={
                                                            managedUser.is_active
                                                                ? UserX
                                                                : UserRound
                                                        }
                                                    >
                                                        {managedUser.is_active
                                                            ? "Deactivate"
                                                            : "Activate"}
                                                    </Button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {!users.length && !usersQuery.isLoading && (
                            <p className="py-10 text-center text-sm text-dark-500">
                                No matching accounts.
                            </p>
                        )}
                        <div className="mt-4 flex items-center justify-between border-t border-dark-800 pt-4 text-xs text-dark-500">
                            <span>Page {page}</span>
                            <div className="flex gap-2">
                                <Button
                                    size="sm"
                                    variant="secondary"
                                    disabled={
                                        !usersQuery.data?.data?.previous || usersQuery.isFetching
                                    }
                                    onClick={() => setPage((current) => Math.max(1, current - 1))}
                                >
                                    Previous
                                </Button>
                                <Button
                                    size="sm"
                                    variant="secondary"
                                    disabled={!usersQuery.data?.data?.next || usersQuery.isFetching}
                                    onClick={() => setPage((current) => current + 1)}
                                >
                                    Next
                                </Button>
                            </div>
                        </div>
                    </>
                )}
            </Card>
        </PageWrapper>
    );
}
