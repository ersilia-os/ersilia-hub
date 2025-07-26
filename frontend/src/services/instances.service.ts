import { HttpClient } from '@angular/common/http';
import { computed, Injectable, Signal, signal, WritableSignal } from '@angular/core';
import { Subscription } from 'rxjs';
import { environment } from '../environments/environment';
import { ModelInstance, ModelInstanceFilters, ModelInstanceFromApi } from '../objects/instance';
import { APIFiltersMap, APIList } from '../objects/common';

@Injectable({
  providedIn: 'root'
})
export class InstancesService {

  private instances: WritableSignal<ModelInstance[]> = signal([]);
  private instancesLoading: WritableSignal<boolean> = signal(false);

  constructor(private http: HttpClient) { }

  loadInstances(filters: ModelInstanceFilters): Subscription {
    this.instancesLoading.set(true);

    return this.http.get<APIList<ModelInstance>>(`${environment.apiHost}/api/instances`, { params: APIFiltersMap(filters) })
      .subscribe(instancesList => {
        let mappedList: ModelInstance[] = instancesList.items.map(ModelInstanceFromApi);
        this.instances.set(mappedList);
        this.instancesLoading.set(false);

        return mappedList;
      });
  }

  getInstancesSignal(): Signal<ModelInstance[]> {
    return computed(() => this.instances());
  }

  computeInstancesSignal<T>(computation: (models: ModelInstance[]) => T): Signal<T> {
    return computed(() => computation(this.instances()));
  }

  getInstancesLoadingSignal(): Signal<boolean> {
    return computed(() => this.instancesLoading());
  }

  computeInstancesLoadingSignal<T>(computation: (loading: boolean) => T): Signal<T> {
    return computed(() => computation(this.instancesLoading()));
  }
}
