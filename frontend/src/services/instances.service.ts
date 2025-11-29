import { HttpClient } from '@angular/common/http';
import { computed, Injectable, Signal, signal, WritableSignal } from '@angular/core';
import { catchError, map, Observable, Subscription, throwError } from 'rxjs';
import { environment } from '../environments/environment';
import { ExtendedModelInstance, ExtendedModelInstanceFromApi, InstanceLogEntry, InstanceLogEntryFromApi, JobLogsFilters, ModelInstance, ModelInstanceFilters, ModelInstanceFromApi } from '../objects/instance';
import { APIFiltersMap, APIList } from '../objects/common';
import { mapHttpError } from '../app/utils/api';

@Injectable({
  providedIn: 'root'
})
export class InstancesService {

  private instances: WritableSignal<ExtendedModelInstance[]> = signal([]);
  private instancesLoading: WritableSignal<boolean> = signal(false);

  constructor(private http: HttpClient) { }

  loadInstances(filters: ModelInstanceFilters): Subscription {
    this.instancesLoading.set(true);

    return this.http.get<APIList<ExtendedModelInstance>>(`${environment.apiHost}/api/instances`, { params: APIFiltersMap(filters) })
      .subscribe(instancesList => {
        let mappedList: ExtendedModelInstance[] = instancesList.items.map(ExtendedModelInstanceFromApi);
        this.instances.set(mappedList);
        this.instancesLoading.set(false);

        return mappedList;
      });
  }

  loadInstanceJobLogs(filters: JobLogsFilters): Observable<string[] | undefined> {
    return this.http.get<{ logs: string[] }>(`${environment.apiHost}/api/instances/job-logs`, { params: APIFiltersMap(filters) })
      .pipe(
        map((response: { logs: string[] }) => {
          return response.logs;
        }),
        catchError(error => {
          const errorString = mapHttpError(error);
          // Return an observable with a user-facing error message.
          return throwError(() => new Error(errorString));
        })
      );
  }

  loadInstanceHistory(filters: ModelInstanceFilters): Observable<InstanceLogEntry[]> {
    return this.http.get<{ history: InstanceLogEntry[] }>(`${environment.apiHost}/api/instances/history`, { params: APIFiltersMap(filters) })
      .pipe(
        map((response: { history: InstanceLogEntry[] }) => {
          return response.history.map(InstanceLogEntryFromApi)
        }),
        catchError(error => {
          const errorString = mapHttpError(error);
          // Return an observable with a user-facing error message.
          return throwError(() => new Error(errorString));
        })
      );
  }

  loadInstance(filters: ModelInstanceFilters): Observable<ExtendedModelInstance | undefined> {
    return this.http.get<APIList<ExtendedModelInstance>>(`${environment.apiHost}/api/instances`, { params: APIFiltersMap(filters) })
      .pipe(
        map((response: APIList<ExtendedModelInstance>) => {
          const items = response.items.map(ExtendedModelInstanceFromApi);

          if (items.length >= 1) {
            return items[0];
          }

          return undefined;
        }),
        catchError(error => {
          const errorString = mapHttpError(error);
          // Return an observable with a user-facing error message.
          return throwError(() => new Error(errorString));
        })
      );
  }

  // TODO: [instanes v2] - /actions api

  getInstancesSignal(): Signal<ExtendedModelInstance[]> {
    return computed(() => this.instances());
  }

  computeInstancesSignal<T>(computation: (models: ExtendedModelInstance[]) => T): Signal<T> {
    return computed(() => computation(this.instances()));
  }

  getInstancesLoadingSignal(): Signal<boolean> {
    return computed(() => this.instancesLoading());
  }

  computeInstancesLoadingSignal<T>(computation: (loading: boolean) => T): Signal<T> {
    return computed(() => computation(this.instancesLoading()));
  }
}
