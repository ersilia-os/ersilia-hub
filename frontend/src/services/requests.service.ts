import { HttpClient } from '@angular/common/http';
import { computed, Injectable, Signal, signal, WritableSignal } from '@angular/core';
import { catchError, map, Observable, Subscription, throwError } from 'rxjs';
import { Request, RequestFilters, RequestFiltersMap, RequestFromApi, RequestList } from '../objects/request';
import { mapHttpError } from '../app/utils/api';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class RequestsService {

  private requests: WritableSignal<Request[]> = signal([]);
  private requestsLoading: WritableSignal<boolean> = signal(false);

  private requestSubmitting: WritableSignal<boolean> = signal(false);
  private requestSubmissionResult: WritableSignal<RequestSubmissionResult | undefined> = signal(undefined);

  constructor(private http: HttpClient) { }

  loadRequests(filters: RequestFilters): Subscription {
    this.requestsLoading.set(true);

    return this.http.get<RequestList>(`${environment.apiHost}/api/work-requests`, {
      params: RequestFiltersMap(filters)
    }).subscribe(requestList => {
      let mappedList: Request[] = requestList.items.map(RequestFromApi);
      this.requests.set(mappedList);
      this.requestsLoading.set(false);

      return mappedList;
    });
  }

  getRequestsSignal(): Signal<Request[]> {
    return computed(() => this.requests());
  }

  computeRequestsSignal<T>(computation: (requests: Request[]) => T): Signal<T> {
    return computed(() => computation(this.requests()));
  }

  getRequestsLoadingSignal(): Signal<boolean> {
    return computed(() => this.requestsLoading());
  }

  computeRequestsLoadingSignal<T>(computation: (loading: boolean) => T): Signal<T> {
    return computed(() => computation(this.requestsLoading()));
  }

  submitRequest(request: Request): Observable<RequestSubmissionResult> {
    this.requestSubmitting.set(true);

    return this.http.post<Request>(`${environment.apiHost}/api/work-requests`, request)
      .pipe(
        map(response => {
          const mappedResponse = RequestFromApi(response);
          const submissionResult = {
            success: true,
            requestResponse: mappedResponse
          };

          this.requestSubmissionResult.set(submissionResult);
          this.requestSubmitting.set(false);

          return submissionResult;
        }),
        catchError(error => {
          const errorString = mapHttpError(error);
          const submissionResult = {
            success: false,
            error: errorString
          };

          this.requestSubmissionResult.set(submissionResult);
          this.requestSubmitting.set(false);

          // Return an observable with a user-facing error message.
          return throwError(() => new Error(errorString));
        })
      );
  }

  getRequestSubmissionResultSignal(): Signal<RequestSubmissionResult | undefined> {
    return computed(() => this.requestSubmissionResult());
  }

  computeRequestSubmissionResultSignal<T>(computation: (result: RequestSubmissionResult | undefined) => T): Signal<T> {
    return computed(() => computation(this.requestSubmissionResult()));
  }

  getRequestSubmittingSignal(): Signal<boolean> {
    return computed(() => this.requestSubmitting());
  }

  computeRequestSubmittingSignal<T>(computation: (loading: boolean) => T): Signal<T> {
    return computed(() => computation(this.requestSubmitting()));
  }

  loadRequest(request_id: string, include_result?: boolean): Observable<Request> {
    return this.http.get<Request>(`${environment.apiHost}/api/work-requests/${request_id}`, {
      params: {
        'include_result': include_result ? include_result : false
      }
    })
      .pipe(
        map(RequestFromApi),
        catchError(error => {
          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }
}

export interface RequestSubmissionResult {
  success: boolean;
  error?: string;
  requestResponse?: Request;
}
