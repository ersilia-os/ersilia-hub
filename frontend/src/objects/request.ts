export enum RequestStatus {
  QUEUED = "QUEUED",
  SCHEDULING = "SCHEDULING",
  PROCESSING = "PROCESSING",
  FAILED = "FAILED",
  COMPLETED = "COMPLETED",
}

export interface RequestPayload {
  entries: string[];
  cache_opt_in: boolean;
}

export interface RequestList {
  items: Request[];
}

export interface Request {
  id?: number;
  model_id: string;
  user_id?: string;
  request_payload: RequestPayload;
  request_date?: Date;
  request_status?: RequestStatus;
  request_status_reason?: string;
  model_job_id?: string;
  last_updated?: Date;
  result?: { [key: string]: object }[];
}

export function RequestFromApi(request: Request): Request {
  return {
    ...request,
    request_date: request.request_date == null ? undefined : new Date(request.request_date),
    last_updated: request.last_updated == null ? undefined : new Date(request.last_updated),
  }
}

export function RequestSubmission(model_id: string, entries: string[], cache_opt_in: boolean = false): Request {
  return {
    model_id: model_id,
    request_payload: {
      entries: entries,
      cache_opt_in: cache_opt_in
    }
  }

}

export interface RequestFilters {
  user_id?: string;
  id?: string;
  model_ids?: string[];
  request_date_from?: Date;
  request_date_to?: Date;
  request_statuses?: string[];
  limit?: number;
}

export function RequestFiltersMap(filters: RequestFilters): { [param: string]: string | number | boolean | ReadonlyArray<string | number | boolean> } {
  return Object.fromEntries(Object.entries(filters));
}
