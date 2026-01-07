import { K8sPodResources } from "./k8s";

export interface ModelList {
  items: Model[];
}

export enum ModelExecutionMode {
  SYNC = "SYNC",
  ASYNC = "ASYNC"
}

export interface ModelIdentificationDetails {
  description?: string;
  title?: string;
  interpretation?: string;
  slug?: string;
  source_code?: string;
  publication?: string;
  target_organisms?: string[]
  biomedical_areas?: string[]
}

export function ModelIdentificationDetails(): ModelIdentificationDetails {
  return {
    description: "",
    title: "",
    interpretation: "",
    slug: "",
    source_code: "",
    publication: "",
    target_organisms: [],
    biomedical_areas: [],
  };
}

export interface ModelDetails {
  template_version: string;
  description: string;
  disable_memory_limit: boolean;
  max_instances: number;
  execution_mode: ModelExecutionMode;
  k8s_resources?: K8sPodResources;
  image_tag: string;
  cache_enabled: boolean;
  identification_details?: ModelIdentificationDetails;
}

export interface Model {
  id: string;
  enabled: boolean;
  details: ModelDetails,
  last_updated?: Date;
}

export function Model(): Model {
  return {
    id: "",
    enabled: true,
    details: {
      template_version: "0.0.0",
      description: "",
      disable_memory_limit: false,
      max_instances: -1,
      execution_mode: ModelExecutionMode.ASYNC,
      k8s_resources: {
        cpu_request: 10,
        cpu_limit: 500,
        memory_request: 100,
        memory_limit: 3500
      },
      image_tag: "latest",
      cache_enabled: false,
      identification_details: ModelIdentificationDetails()
    }
  }
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

export interface ModelFilter {
  id: string | undefined;
  description: string | undefined;
}

export function filterModels(models: Model[], filters: ModelFilter): Model[] {
  return models.filter(model =>
    checkId(model, filters.id)
    && checkDescription(model, filters.description)
  )
}

export function checkId(model: Model, filter: string | undefined): boolean {
  return filter == null || (model.id != null && model.id.includes(filter));
}

export function checkDescription(model: Model, filter: string | undefined): boolean {
  return filter == null || (model.details.description != null && model.details.description.includes(filter));
}
