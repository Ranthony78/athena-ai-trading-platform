import { useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { Card, Badge, Button } from "../../../components/common";
import { journalAPI } from "../../../api/journal";

export default function LessonCard({ lesson }) {
    const queryClient = useQueryClient();
    const { mutate: reinforce } = useMutation({
        mutationFn: () => journalAPI.reinforceLesson(lesson.id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lessons"] }),
    });

    return (
        <Card>
            <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                    <Badge variant={lesson.is_rule ? "red" : "blue"}>
                        {lesson.is_rule ? "RULE" : lesson.category}
                    </Badge>
                </div>
                <Button variant="ghost" size="sm" icon={RefreshCw} onClick={() => reinforce()}>
                    {lesson.times_reinforced}x
                </Button>
            </div>
            <h3 className="text-sm font-semibold text-dark-100 mb-1">{lesson.title}</h3>
            <p className="text-xs text-dark-400">{lesson.content}</p>
        </Card>
    );
}