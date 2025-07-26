export interface ModelInstanceFilters {
    active?: boolean;
    persisted?: boolean;
    model_id?: string;
    instance_id?: string
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
    running_averages: RunningAverages;

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

export interface K8sPod {
    name: string;
    state: K8sPodContainerState;
    ip: string;
    labels: { [key: string]: string };
    annotations: { [key: string]: string };
    pod_state: K8sPodState;
    node_name?: string;
    resources: K8sPodResources;
}

export interface K8sPodContainerState {
    phase: string;
    started: boolean;
    ready: boolean;
    restart_count: number;
    state_times: { [key: string]: string };
    last_state_times: { [key: string]: string };
}

export interface K8sPodCondition {
    last_probe_time: string;
    last_transition_time: string;
    message: string;
    reason: string;
    status: string;
    type: string;
}

export interface K8sPodState {
    conditions: K8sPodCondition[];
    message: string;
    reason: string;
    start_time: string;
}

export interface K8sPodResources {
    cpu_request: number; // in millicores
    cpu_limit?: number; // in millicores
    memory_request: number; // in megabytes
    memory_limit?: number; // in megabytes
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