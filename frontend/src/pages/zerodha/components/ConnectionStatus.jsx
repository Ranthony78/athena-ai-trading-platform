import { CheckCircle, XCircle } from "lucide-react";
import { Card, Badge } from "../../../components/common";
import { formatDateTime } from "../../../utils/formatters";

export default function ConnectionStatus({ status }) {
    if (!status) return null;

    return (
        <Card title="Connection Status">
            <div className="flex items-center gap-3 mb-4">
                {status.is_connected ? (
                    <CheckCircle className="w-8 h-8 text-green-400" />
                ) : (
                    <XCircle className="w-8 h-8 text-red-400" />
                )}
                <div>
                    <p className={`text-lg font-bold
            ${status.is_connected ? "text-green-400" : "text-red-400"}`}>
                        {status.is_connected ? "Connected" : "Not Connected"}
                    </p>
                    {status.zerodha_username && (
                        <p className="text-sm text-dark-400">
                            {status.zerodha_username} ({status.zerodha_user_id})
                        </p>
                    )}
                </div>
            </div>

            {status.is_connected && (
                <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                        <span className="text-dark-500">Connected At</span>
                        <span className="text-dark-200">
                            {formatDateTime(status.connected_at)}
                        </span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-dark-500">Token Valid</span>
                        <Badge variant={status.is_token_valid ? "green" : "red"}>
                            {status.is_token_valid ? "Yes" : "Expired"}
                        </Badge>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-dark-500">Expires At</span>
                        <span className="text-dark-200">
                            {formatDateTime(status.token_expires_at)}
                        </span>
                    </div>
                </div>
            )}
        </Card>
    );
}