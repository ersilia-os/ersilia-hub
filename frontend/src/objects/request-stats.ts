
export interface WorkRequestStatsFilterData {
    model_ids: string[];
    group_by: string[];
}

export interface WorkRequestStats {
    model_id: string;
    input_size: number;
    total_count: number;
    success_count: number;
    failed_count: number;

    total_all_request_start_time: number;
    max_all_request_start_time: number;
    min_all_request_start_time: number;
    avg_all_request_start_time: number;

    total_all_request_time: number;
    max_all_request_time: number;
    min_all_request_time: number;
    avg_all_request_time: number;

    total_all_job_execution_time: number;
    max_all_job_execution_time: number;
    min_all_job_execution_time: number;
    avg_all_job_execution_time: number;

    total_success_request_start_time: number;
    max_success_request_start_time: number;
    min_success_request_start_time: number;
    avg_success_request_start_time: number;

    total_success_request_time: number;
    max_success_request_time: number;
    min_success_request_time: number;
    avg_success_request_time: number;

    total_success_job_execution_time: number;
    max_success_job_execution_time: number;
    min_success_job_execution_time: number;
    avg_success_job_execution_time: number;

    total_failed_request_start_time: number;
    max_failed_request_start_time: number;
    min_failed_request_start_time: number;
    avg_failed_request_start_time: number;

    total_failed_request_time: number;
    max_failed_request_time: number;
    min_failed_request_time: number;
    avg_failed_request_time: number;

    total_failed_job_execution_time: number;
    max_failed_job_execution_time: number;
    min_failed_job_execution_time: number;
    avg_failed_job_execution_time: number;
}


export interface WorkRequestStatsList {
    stats: WorkRequestStats[];
}

export interface WorkRequestStatsFilters {
    user_id?: string;
    session_id?: string;
    model_ids?: string[];
    request_date_from?: string;
    request_date_to?: string;
    request_statuses?: string[];
    input_size_ge?: number;
    input_size_le?: number;
    group_by?: string[];
}


export function WorkRequestStatsFiltersMap(filters: WorkRequestStatsFilters): { [param: string]: string | number | boolean | ReadonlyArray<string | number | boolean> } {
    return Object.fromEntries(Object.entries(filters));
}
