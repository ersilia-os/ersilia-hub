import { K8sPod } from "./k8s";
import { ModelInstanceRecommendations, ModelInstanceResourceProfile } from "./recommendations";
import { Request } from "./request.ts"

export interface ModelInstanceFilters {
  states?: (string | ModelInstanceState)[];
  not_states?: (string | ModelInstanceState)[];
  model_id?: string;
  work_request_id?: string;
  instance_id?: string;
  load_resource_profiles?: boolean;
  load_recommendations?: boolean;
}

export enum ModelInstanceState {
  REQUESTED = "REQUESTED",
  INITIALIZING = "INITIALIZING",
  WAITING_FOR_READINESS = "WAITING_FOR_READINESS",
  ACTIVE = "ACTIVE",
  SHOULD_TERMINATE = "SHOULD_TERMINATE",
  TERMINATING = "TERMINATING",
  TERMINATED = "TERMINATED"
}

export enum ModelInstanceTerminationReason {
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  OOMKILLED = "OOMKILLED"
}

export enum InstanceActionEnum {
  STOP_INSTANCE = "STOP_INSTANCE"
}

export interface ModelInstance {
  model_id: string;
  work_request_id: number;
  instance_id?: string;
  instance_details?: K8sPod;
  state: ModelInstanceState;
  termination_reason?: ModelInstanceTerminationReason;
  job_submission_process?: JobSubmissionProcess;
  last_updated?: Date;
}

export function ModelInstanceFromApi(obj: ModelInstance): ModelInstance {
  return {
    ...obj,
    last_updated: obj.last_updated ? new Date(obj.last_updated) : undefined
  };
}

export interface ExtendedModelInstance {
  model_instance: ModelInstance;
  last_event?: InstanceLogEntry;
  work_request?: Request;
  metrics?: InstanceMetrics;
  resource_profile?: ModelInstanceResourceProfile;
  resource_recommendations?: ModelInstanceRecommendations;
}

export function ExtendedModelInstanceFromApi(obj: ExtendedModelInstance): ExtendedModelInstance {
  return {
    ...obj,
    model_instance: ModelInstanceFromApi(obj.model_instance),
    last_event: obj.last_event ? InstanceLogEntryFromApi(obj.last_event) : undefined
  };
}

export interface JobLogsFilters {
  model_id?: string;
  work_request_id?: string;
  tail?: number;
  head?: number;
}

export interface InstanceAction {
  model_id?: string;
  work_request_id?: string;
  action: string;
}

export interface InstanceLogEntry {
  model_id: string;
  instance_id: string;
  correlation_id: string;
  instance_details?: K8sPod;
  log_event: string;
  log_timestamp: Date;
}

export function InstanceLogEntryFromApi(obj: InstanceLogEntry): InstanceLogEntry {
  return {
    ...obj,
    log_timestamp: new Date(obj.log_timestamp)
  }
}

export interface InstanceMetrics {
  model_id: string;
  instance_id: string;
  namespace: string;
  cpu_running_averages: RunningAverages;
  memory_running_averages: RunningAverages;
}

export interface RunningAverages {
  count: number;
  total: number;
  min: number;
  max: number;
  avg: number;
  count_60s: number;
  total_60s: number;
  min_60s: number;
  max_60s: number;
  avg_60s: number;
}

export interface JobSubmissionProcess {
  model_id: string;
  work_request_id: string;
  id: string;
  job_entries: string[];
  retry_count: number;
  model_execution_mode: string;
  job_id?: string;
  job_status: string;
  job_status_reason?: string;
  job_submission_timestamp?: string;
  job_completion_timestamp?: string;
}

