import { K8sPodResources } from "./k8s";

export interface ModelList {
    items: Model[];
}

export enum ModelExecutionMode {
    SYNC = "SYNC",
    ASYNC = "ASYNC"
}

export interface ModelDetails {
    template_version: string;
    description: string;
    disable_memory_limit: boolean;
    max_instances: number;
    execution_mode: ModelExecutionMode;
    k8s_resources?: K8sPodResources;
}

export interface Model {
    id: string;
    enabled: boolean;
    details: ModelDetails,
    last_updated?: Date;
}

export function ModelFromApi(model: Model): Model {
    return {
        ...model,
        last_updated: model.last_updated == null ? undefined : new Date(model.last_updated),
    }
}

export interface ModelUpdate {
    id: string;
    details: ModelDetails;
    enabled: boolean;
}
