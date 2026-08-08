import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Copy } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Badge, Button, Modal, Input, Select, Spinner } from "../../components/common";
import { knowledgeAPI } from "../../api/knowledge";

export default function Prompts() {
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({ title: "", content: "", prompt_type: "CUSTOM", description: "" });
    const queryClient = useQueryClient();

    const { data: prompts, isLoading } = useQuery({
        queryKey: ["prompts"],
        queryFn: () => knowledgeAPI.getPrompts(),
        select: (res) => res.data.data,
    });

    const { mutate: create, isPending } = useMutation({
        mutationFn: (data) => knowledgeAPI.createPrompt(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["prompts"] });
            setShowModal(false);
        },
    });

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
    };

    return (
        <PageWrapper
            title="Prompt Library"
            subtitle="Reusable AI prompts"
            actions={
                <Button variant="primary" size="sm" icon={Plus}
                    onClick={() => setShowModal(true)}>
                    Add Prompt
                </Button>
            }
        >
            {isLoading ? <Spinner /> : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {(prompts || []).map((prompt) => (
                        <Card key={prompt.id}>
                            <div className="flex items-start justify-between mb-2">
                                <Badge variant="blue">{prompt.prompt_type}</Badge>
                                <Button variant="ghost" size="sm" icon={Copy}
                                    onClick={() => copyToClipboard(prompt.content)}>
                                    Copy
                                </Button>
                            </div>
                            <h3 className="text-sm font-semibold text-dark-100 mb-1">
                                {prompt.title}
                            </h3>
                            {prompt.description && (
                                <p className="text-xs text-dark-400 mb-2">{prompt.description}</p>
                            )}
                            <pre className="text-xs text-dark-400 bg-dark-800 rounded p-2
                              overflow-hidden max-h-20 whitespace-pre-wrap">
                                {prompt.content}
                            </pre>
                            <p className="text-xs text-dark-600 mt-2">
                                Used {prompt.use_count} times
                            </p>
                        </Card>
                    ))}
                </div>
            )}

            <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Add Prompt">
                <div className="space-y-4">
                    <Input label="Title" value={form.title}
                        onChange={(e) => setForm(f => ({ ...f, title: e.target.value }))} />
                    <Select label="Type"
                        options={["ANALYSIS", "RESEARCH", "STRATEGY", "REVIEW", "LEARNING", "CUSTOM"]
                            .map(v => ({ value: v, label: v }))}
                        value={form.prompt_type}
                        onChange={(e) => setForm(f => ({ ...f, prompt_type: e.target.value }))}
                    />
                    <div>
                        <label className="label">Prompt Content</label>
                        <textarea className="input h-32 resize-none font-mono text-xs"
                            value={form.content}
                            onChange={(e) => setForm(f => ({ ...f, content: e.target.value }))} />
                    </div>
                    <Button variant="primary" loading={isPending}
                        onClick={() => create(form)} className="w-full">
                        Save Prompt
                    </Button>
                </div>
            </Modal>
        </PageWrapper>
    );
}