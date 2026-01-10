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
  freeText: string | undefined;
  id: string | undefined;
  description: string | undefined;
}

export function filterModels(models: Model[], filters: ModelFilter): Model[] {
  if (filters == null) {
    return [...models];
  }

  const sanitisedFilters = {
    id: filters.id ? filters.id.toLowerCase() : undefined,
    description: filters.description ? filters.description.toLowerCase() : undefined,
    freeText: filters.freeText ? filters.freeText.toLowerCase() : undefined,
  }

  return models.filter(model =>
    (sanitisedFilters.id == null || filterById(model, sanitisedFilters.id))
    && (sanitisedFilters.description == null || filterByDescription(model, sanitisedFilters.description))
    && (sanitisedFilters.freeText == null || filterByFreetext(model, sanitisedFilters.freeText))
  );
}

function filterByFreetext(model: Model, filter: string): boolean {
  return model.id != null && model.id.includes(filter)
    || model.details != null && (
      model.details.description != null && model.details.description.toLowerCase().includes(filter)
      || model.details.identification_details != null && (
        model.details.identification_details.slug != null && model.details.identification_details.slug.toLowerCase().includes(filter)
        || model.details.identification_details.title != null && model.details.identification_details.title.toLowerCase().includes(filter)
        || model.details.identification_details.interpretation != null && model.details.identification_details.interpretation.toLowerCase().includes(filter)
        || model.details.identification_details.biomedical_areas != null && model.details.identification_details.biomedical_areas.some(f => f.toLowerCase().includes(filter))
        || model.details.identification_details.target_organisms != null && model.details.identification_details.target_organisms.some(f => f.toLowerCase().includes(filter))
      )
    )
}

export function filterById(model: Model, filter: string | undefined): boolean {
  return filter == null || (model.id != null && model.id.includes(filter));
}

export function filterByDescription(model: Model, filter: string | undefined): boolean {
  return filter == null || (model.details.description != null && model.details.description.includes(filter));
}
