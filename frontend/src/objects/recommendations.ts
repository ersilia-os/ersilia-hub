
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
    current_allocation_percentage: number;
    current_allocation_profile_state: ResourceProfileConfig;
    recommended_value: number;
}

export interface ModelInstanceRecommendations {
    model_id?: string;
    cpu_min: ResourceRecommendation;
    cpu_max: ResourceRecommendation;
    memory_min: ResourceRecommendation;
    memory_max: ResourceRecommendation;
    profiled_instances: string[];
    last_updated?: Date;
}

export function ModelInstanceRecommendationsFromAPI(object: ModelInstanceRecommendations): ModelInstanceRecommendations {
    return {
        ...object,
        last_updated: new Date(object.last_updated ?? 0)
    }
}

export interface RecommendationEngineState {
    last_updated?: Date;
    model_recommendations: ModelInstanceRecommendations[];
}

export interface RecommendationsLoadFilters {
    model_ids?: string[];
}


export interface ApplyRecommendations {
    recommendations: ModelInstanceRecommendations;
    profiles?: ResourceProfileId[];
}
