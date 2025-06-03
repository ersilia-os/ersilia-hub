
export interface ModelList {
    items: Model[];
}

export interface ModelDetails {
    template_version: string;
    description: string;
    size_megabytes: number;
    disable_memory_limit: boolean;
    max_instances: number
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