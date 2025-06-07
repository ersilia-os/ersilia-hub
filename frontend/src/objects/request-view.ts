import { Request, RequestPayload, RequestStatus } from './request';

export interface RequestDisplay {
    id?: string;
    model_id: string;
    request_payload?: string;
    request_date?: Date;
    request_status?: RequestStatus;
    request_status_reason?: string;
    last_updated?: Date;
    has_result: boolean;
}

export function mapRequest(request: Request): RequestDisplay {
    request.request_status?.toLowerCase
    return {
        id: `${request.id}`,
        model_id: request.model_id,
        request_payload:
            (request.request_payload == null || request.request_payload.entries == null || request.request_payload.entries.length === 0)
                ? undefined : request.request_payload.entries.join("\n"),
        request_date: request.request_date,
        request_status: request.request_status,
        request_status_reason: request.request_status_reason,
        last_updated: request.last_updated,
        has_result: request.request_status == RequestStatus.COMPLETED
    };
}