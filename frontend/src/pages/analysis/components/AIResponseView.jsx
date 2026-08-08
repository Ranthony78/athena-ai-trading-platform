import { Card } from "../../../components/common";

export default function AIResponseView({ response }) {
    if (!response) return null;

    return (
        <Card title="AI Analysis">
            <div className="prose prose-invert prose-sm max-w-none">
                <pre className="whitespace-pre-wrap text-sm text-dark-200
                        font-sans leading-relaxed bg-dark-800
                        rounded-lg p-4 overflow-auto max-h-96">
                    {response}
                </pre>
            </div>
        </Card>
    );
}