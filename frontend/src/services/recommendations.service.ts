import { HttpClient } from '@angular/common/http';
import { computed, Injectable, Signal, signal, WritableSignal } from '@angular/core';
import { Subscription } from 'rxjs';
import { environment } from '../environments/environment';
import { APIFiltersMap } from '../objects/common';
import { ModelInstanceRecommendations, ModelInstanceRecommendationsFromAPI, RecommendationEngineState, RecommendationsLoadFilters, ResourceProfileId } from '../objects/recommendations';

@Injectable({
  providedIn: 'root'
})
export class RecommendationsService {

  private recommendationsLastUpdated: WritableSignal<Date> = signal(new Date(0));
  private recommendations: WritableSignal<ModelInstanceRecommendations[]> = signal([]);
  private recommendationsLoading: WritableSignal<boolean> = signal(false);

  constructor(private http: HttpClient) { }

  /**
   * Load all recommendations (filtered) and update the full list
   */
  loadRecommendations(filters?: RecommendationsLoadFilters): Subscription {
    this.recommendationsLoading.set(true);

    return this.http.get<RecommendationEngineState>(`${environment.apiHost}/api/recommendations`, { params: APIFiltersMap(filters ?? {}) })
      .subscribe(engineState => {
        let mappedList: ModelInstanceRecommendations[] = engineState.model_recommendations.map(ModelInstanceRecommendationsFromAPI);
        this.recommendations.set(mappedList);
        this.recommendationsLastUpdated.set(new Date(engineState.last_updated ?? 0));

        this.recommendationsLoading.set(false);

        return mappedList;
      });
  }

  private updateModelRecommendation(recommendation: ModelInstanceRecommendations) {
    let currentRecommendations = this.recommendations();
    let modelIndex = currentRecommendations.findIndex(model => model.model_id === recommendation.model_id);

    if (modelIndex < 0) {
      currentRecommendations.push(recommendation);
    } else {
      currentRecommendations = [
        ...currentRecommendations.slice(0, modelIndex),
        recommendation,
        ...currentRecommendations.slice(modelIndex + 1)
      ];
    }

    this.recommendations.set(currentRecommendations);
  }

  /**
   * Load single recommendation and update existing recommendations list in-place
   */
  loadModelRecommendations(modelId: string): Subscription {
    this.recommendationsLoading.set(true);

    return this.http.get<RecommendationEngineState>(`${environment.apiHost}/api/recommendations`, { params: APIFiltersMap({ model_id: [modelId] }) })
      .subscribe(engineState => {
        if (engineState.model_recommendations.length <= 0) {
          this.recommendationsLoading.set(false);

          return
        }

        let mappedList: ModelInstanceRecommendations[] = engineState.model_recommendations.map(ModelInstanceRecommendationsFromAPI);
        this.updateModelRecommendation(mappedList[0]);
        this.recommendationsLoading.set(false);

        return mappedList[0];
      });
  }

  applyModelRecommendations(recommendations: ModelInstanceRecommendations, profiles?: ResourceProfileId[]): Subscription {
    this.recommendationsLoading.set(true);

    return this.http.post<ModelInstanceRecommendations>(`${environment.apiHost}/api/recommendations/apply`, {
      recommendations: recommendations,
      profiles: profiles
    })
      .subscribe(updatedRecommendations => {
        const mapped = ModelInstanceRecommendationsFromAPI(updatedRecommendations);
        this.updateModelRecommendation(mapped);
        this.recommendationsLoading.set(false);

        return mapped;
      });
  }

  getRecommendationsLastUpdated(): Signal<Date> {
    return computed(() => this.recommendationsLastUpdated());
  }

  computeRecommendationsLastUpdated<T>(computation: (date: Date) => T): Signal<T> {
    return computed(() => computation(this.recommendationsLastUpdated()));
  }

  getRecommendations(): Signal<ModelInstanceRecommendations[]> {
    return computed(() => this.recommendations());
  }

  computeRecommendations<T>(computation: (recommendations: ModelInstanceRecommendations[]) => T): Signal<T> {
    return computed(() => computation(this.recommendations()));
  }

  getRecommendationsLoadingSignal(): Signal<boolean> {
    return computed(() => this.recommendationsLoading());
  }

  computeRecommendationsLoadingSignal<T>(computation: (loading: boolean) => T): Signal<T> {
    return computed(() => computation(this.recommendationsLoading()));
  }
}
