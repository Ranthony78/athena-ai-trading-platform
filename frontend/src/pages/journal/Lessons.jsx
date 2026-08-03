import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, BookOpen } from "lucide-react";
import { PageWrapper } from "../../components/layout";
import { Card, Button, Badge, Modal, Spinner, EmptyState } from "../../components/common";
import LessonCard from "./components/LessonCard";
import { journalAPI } from "../../api/journal";

export default function Lessons() {
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({ title: "", content: "", category: "GENERAL", is_rule: false });
    const queryClient = useQueryClient();

    const { data: lessons, isLoading } = useQuery({
        queryKey: ["lessons"],
        queryFn: () => journalAPI.getLessons(),
        select: (res) => res.data.data,
    });

    const { mutate: add, isPending } = useMutation({
        mutationFn: (data) => journalAPI.addLesson(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["lessons"] });
            setShowModal(false);
        },
    });

    return (
        <PageWrapper
            title="Lessons & Rules"
            subtitle="Your personal trading wisdom"
            actions={
                <Button variant="primary" size="sm" icon={Plus} onClick={() => setShowModal(true)}>
                    Add Lesson
                </Button>
            }
        >
            {isLoading ? (
                <Spinner />
            ) : !lessons?.length ? (
                <EmptyState icon={BookOpen} title="No lessons yet" />
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {lessons.map((lesson) => (
                        <LessonCard key={lesson.id} lesson={lesson} />
                    ))}
                </div>
            )}

            <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Add Lesson">
                <div className="space-y-4">
                    <div>
                        <label className="label">Title</label>
                        <input className="input" value={form.title}
                            onChange={(e) => setForm(f => ({ ...f, title: e.target.value }))} />
                    </div>
                    <div>
                        <label className="label">Content</label>
                        <textarea className="input h-24 resize-none" value={form.content}
                            onChange={(e) => setForm(f => ({ ...f, content: e.target.value }))} />
                    </div>
                    <div className="flex items-center gap-2">
                        <input type="checkbox" checked={form.is_rule}
                            onChange={(e) => setForm(f => ({ ...f, is_rule: e.target.checked }))} />
                        <label className="text-sm text-dark-300">Mark as hard rule</label>
                    </div>
                    <Button variant="primary" loading={isPending} onClick={() => add(form)}
                        className="w-full">
                        Save Lesson
                    </Button>
                </div>
            </Modal>
        </PageWrapper>
    );
}