import { HttpClient } from '@angular/common/http';
import { computed, Injectable, Signal, signal, WritableSignal } from '@angular/core';
import { Subscription } from 'rxjs';
import { Model, ModelFromApi, ModelList } from '../objects/model';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ModelsService {

  private models: WritableSignal<Model[]> = signal([]);
  private modelsLoading: WritableSignal<boolean> = signal(false);

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
}
