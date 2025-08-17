import { K8sPod } from "./k8s";
import { ModelInstanceRecommendations, ModelInstanceResourceProfile } from "./recommendations";

export interface ModelInstanceFilters {
    active?: boolean;
    persisted?: boolean;
    model_id?: string;
    instance_id?: string
    load_resource_profiles?: boolean;
    load_recommendations?: boolean;
}

export enum ModelInstanceState {
    STARTING = "STARTING",
    RUNNING = "RUNNING",
    TERMINATING = "TERMINATING",
    TERMINATED = "TERMINATED",
    ERROR = "ERROR",
    UNKNOWN = "UNKNOWN"
}

export interface ModelInstance {
    k8s_pod: K8sPod;
    metrics?: InstanceMetrics;
    resource_profile?: ModelInstanceResourceProfile;
    resource_recommendations?: ModelInstanceRecommendations;

    // details not on API
    is_model?: boolean;
    request_id?: string;
    model_id?: string;
    instance_state?: ModelInstanceState;
    instance_state_reason?: string;
}

export function ModelInstanceFromApi(obj: ModelInstance): ModelInstance {
    // TODO: map date fields

    let requestId = obj.k8s_pod.annotations["ersilia.requestid"];
    let modelId = obj.k8s_pod.labels["ersilia.modelid"];

    let instanceState: ModelInstanceState = ModelInstanceState.UNKNOWN;
    let instanceStateReason = undefined;

    if (obj.k8s_pod.state.phase === "Pending") {
        instanceState = ModelInstanceState.STARTING;
    } else if (obj.k8s_pod.state.phase === "Running") {
        instanceState = ModelInstanceState.RUNNING;
    } else if (obj.k8s_pod.state.phase === "Failed") {
        instanceState = ModelInstanceState.ERROR;
        // TODO: get error from conditions
    }
    // TODO: termination ??

    return {
        ...obj,
        is_model: requestId != null || modelId != null,
        request_id: requestId,
        model_id: modelId,
        instance_state: instanceState,
        instance_state_reason: instanceStateReason
    };
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
