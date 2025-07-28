
export interface ResourceProfile {
    min_usage: number;
    min_allocatable: number;
    min_usage_percentage: number;
    max_usage: number;
    max_allocatable: number;
    max_usage_percentage: number;
}

export interface ModelInstanceResourceProfile {
    cpu: ResourceProfile;
    memory: ResourceProfile;
}

export enum ResourceProfileId {
    CPU_MIN = "CPU_MIN",
    CPU_MAX = "CPU_MAX",
    MEMORY_MIN = "MEMORY_MIN",
    MEMORY_MAX = "MEMORY_MAX"
}

export enum ResourceProfileState {
    VERY_UNDER = "VERY_UNDER",
    UNDER = "UNDER",
    RECOMMENDED = "RECOMMENDED",
    OVER = "OVER",
    VERY_OVER = "VERY_OVER"
}

export interface ResourceProfileConfig {
    id: ResourceProfileId;
    state: ResourceProfileState;
    min: number;
    max: number;
}

export interface ResourceRecommendation {
    profile_id: ResourceProfileId;
    current_usage_value: number;
    current_allocation_value: number;
    current_usage_percentage: number;
    current_profile_state: ResourceProfileConfig;
    recommended_profile: ResourceProfileConfig;
    recommended_min_value: number;
    recommended_max_value: number;
}

export interface ModelInstanceRecommendations {
    cpu_min: ResourceRecommendation;
    cpu_max: ResourceRecommendation;
    memory_min: ResourceRecommendation;
    memory_max: ResourceRecommendation;
}