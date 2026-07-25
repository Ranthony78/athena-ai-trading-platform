import { Brain } from "lucide-react";
import { Card } from "../../../components/common";

export default function AIReviewCard({ review }) {
    return (
        <Card title="AI Review" actions={<Brain className="w-4 h-4 text-primary-400" />}>
            <p className="text-sm text-dark-300 whitespace-pre-wrap leading-relaxed">
                {review}
            </p>
        </Card>
    );
}