import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Shield, Plus } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Badge, Button, Modal, Input, Select, Spinner, EmptyState } from "../../components/common";
import { knowledgeAPI } from "../../api/knowledge";

export default function Rules() {
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({
        title: "", description: "",
        rule_type: "SYSTEM", priority: "HIGH",
    });
    const queryClient = useQueryClient();

    const { data: rules, isLoading } = useQuery({
        queryKey: ["trading-rules"],
        queryFn: () => knowledgeAPI.getRules(),
        select: (res) => res.data.data,
    });

    const { mutate: create, isPending } = useMutation({
        mutationFn: (data) => knowledgeAPI.createRule(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["trading-rules"] });
            setShowModal(false);
        },
    });

    const { mutate: recordBroken } = useMutation({
        mutationFn: (id) => knowledgeAPI.recordRuleBroken(id),
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ["trading-rules"] }),
    });

    return (
        <PageWrapper
            title="Trading Rules"
            subtitle="Your personal rulebook"
            actions={
                <Button variant="primary" size="sm" icon={Plus}
                    onClick={() => setShowModal(true)}>
                    Add Rule
                </Button>
            }
        >
            {isLoading ? <Spinner /> : !rules?.length ? (
                <EmptyState icon={Shield} title="No rules yet"
                    description="Define your trading rules" />
            ) : (
                <div className="space-y-3">
                    {rules.map((rule) => (
                        <Card key={rule.id}>
                            <div className="flex items-start justify-between">
                                <div className="flex items-start gap-3">
                                    <span className="text-2xl font-bold text-dark-700 font-mono">
                                        #{rule.rule_number}
                                    </span>
                                    <div>
                                        <h3 className="text-sm font-semibold text-dark-100">
                                            {rule.title}
                                        </h3>
                                        <p className="text-xs text-dark-400 mt-1">
                                            {rule.description}
                                        </p>
                                        <div className="flex gap-2 mt-2">
                                            <Badge variant={
                                                rule.priority === "CRITICAL" ? "red" :
                                                    rule.priority === "HIGH" ? "yellow" : "gray"
                                            }>
                                                {rule.priority}
                                            </Badge>
                                            <Badge variant="blue">{rule.rule_type}</Badge>
                                        </div>
                                    </div>
                                </div>
                                <Button variant="ghost" size="sm"
                                    onClick={() => recordBroken(rule.id)}
                                    className="text-red-400 hover:text-red-300">
                                    Broken ({rule.times_broken})
                                </Button>
                            </div>
                        </Card>
                    ))}
                </div>
            )}

            <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Add Rule">
                <div className="space-y-4">
                    <Input label="Rule Title" value={form.title}
                        onChange={(e) => setForm(f => ({ ...f, title: e.target.value }))} />
                    <div>
                        <label className="label">Description</label>
                        <textarea className="input h-20 resize-none" value={form.description}
                            onChange={(e) => setForm(f => ({ ...f, description: e.target.value }))} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <Select label="Type"
                            options={["ENTRY", "EXIT", "RISK", "PSYCHOLOGY", "SYSTEM"].map(v => ({ value: v, label: v }))}
                            value={form.rule_type}
                            onChange={(e) => setForm(f => ({ ...f, rule_type: e.target.value }))}
                        />
                        <Select label="Priority"
                            options={["CRITICAL", "HIGH", "MEDIUM", "LOW"].map(v => ({ value: v, label: v }))}
                            value={form.priority}
                            onChange={(e) => setForm(f => ({ ...f, priority: e.target.value }))}
                        />
                    </div>
                    <Button variant="primary" loading={isPending}
                        onClick={() => create(form)} className="w-full">
                        Save Rule
                    </Button>
                </div>
            </Modal>
        </PageWrapper>
    );
}