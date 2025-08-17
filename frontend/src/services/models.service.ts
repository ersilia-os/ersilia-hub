import { HttpClient } from '@angular/common/http';
import { computed, Injectable, Signal, signal, WritableSignal } from '@angular/core';
import { catchError, map, Observable, Subscription, throwError } from 'rxjs';
import { Model, ModelFromApi, ModelList, ModelUpdate } from '../objects/model';
import { environment } from '../environments/environment';
import { mapHttpError } from '../app/utils/api';

@Injectable({
  providedIn: 'root'
})
export class ModelsService {

  private models: WritableSignal<Model[]> = signal([]);
  private modelsLoading: WritableSignal<boolean> = signal(false);

  private modelSubmitting: WritableSignal<boolean> = signal(false);
  private modelSubmissionResult: WritableSignal<ModelSubmissionResult | undefined> = signal(undefined);

  constructor(private http: HttpClient) { }

  loadModels(): Subscription {
    this.modelsLoading.set(true);

    return this.http.get<ModelList>(`${environment.apiHost}/api/models`).subscribe(modelsList => {
      let mappedList: Model[] = modelsList.items.map(ModelFromApi);
      this.models.set(mappedList);
      this.modelsLoading.set(false);

      return mappedList;
    });
  }

  private updateModels(model: Model) {
    let currentModels = this.models();
    let modelIndex = currentModels.findIndex(currModel => currModel.id === model.id);

    if (modelIndex < 0) {
      currentModels.push(model);
    } else {
      currentModels = [
        ...currentModels.slice(0, modelIndex),
        model,
        ...currentModels.slice(modelIndex + 1)
      ];
    }

    this.models.set(currentModels);
  }

  createModel(model: Model): Observable<ModelSubmissionResult> {
    if (this.modelSubmitting()) {
      return throwError(() => new Error("Already submitting"));
    }

    this.modelSubmitting.set(true);

    return this.http.post<Model>(`${environment.apiHost}/api/models`, model)
      .pipe(
        map((updatedModel: Model) => {
          const mapped = ModelFromApi(updatedModel);
          this.updateModels(mapped);

          const submissionResult = {
            success: true,
            response: mapped
          };

          this.modelSubmissionResult.set(submissionResult);
          this.modelSubmitting.set(false);

          return submissionResult;
        }),
        catchError(error => {
          const errorString = mapHttpError(error);
          const submissionResult = {
            success: false,
            error: errorString
          };

          this.modelSubmissionResult.set(submissionResult);
          this.modelSubmitting.set(false);

          // Return an observable with a user-facing error message.
          return throwError(() => new Error(errorString));
        })
      );
  }

  updateModel(modelUpdate: ModelUpdate): Observable<ModelSubmissionResult> {
    if (this.modelSubmitting()) {
      return throwError(() => new Error("Already submitting"));
    }

    this.modelSubmitting.set(true);

    return this.http.put<Model>(`${environment.apiHost}/api/models/${modelUpdate.id}`, modelUpdate)
      .pipe(
        map((updatedModel: Model) => {
          const mapped = ModelFromApi(updatedModel);
          this.updateModels(mapped);

          const submissionResult = {
            success: true,
            response: mapped
          };

          this.modelSubmissionResult.set(submissionResult);
          this.modelSubmitting.set(false);

          return submissionResult;
        }),
        catchError(error => {
          const errorString = mapHttpError(error);
          const submissionResult = {
            success: false,
            error: errorString
          };

          this.modelSubmissionResult.set(submissionResult);
          this.modelSubmitting.set(false);

          // Return an observable with a user-facing error message.
          return throwError(() => new Error(errorString));
        })
      );
  }

  getModelsSignal(): Signal<Model[]> {
    return computed(() => this.models());
  }

  computeModelsSignal<T>(computation: (models: Model[]) => T): Signal<T> {
    return computed(() => computation(this.models()));
  }

  getModelsLoadingSignal(): Signal<boolean> {
    return computed(() => this.modelsLoading());
  }

  computeModelsLoadingSignal<T>(computation: (loading: boolean) => T): Signal<T> {
    return computed(() => computation(this.modelsLoading()));
  }

  getModelSubmissionResultSignal(): Signal<ModelSubmissionResult | undefined> {
    return computed(() => this.modelSubmissionResult());
  }

  computeModelSubmissionResultSignal<T>(computation: (result: ModelSubmissionResult | undefined) => T): Signal<T> {
    return computed(() => computation(this.modelSubmissionResult()));
  }

  getModelSubmittingSignal(): Signal<boolean> {
    return computed(() => this.modelSubmitting());
  }

  computeModelSubmittingSignal<T>(computation: (loading: boolean) => T): Signal<T> {
    return computed(() => computation(this.modelSubmitting()));
  }
}

export interface ModelSubmissionResult {
  success: boolean;
  error?: string;
  response?: Model;
}