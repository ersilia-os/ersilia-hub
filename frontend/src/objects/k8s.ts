
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