import { HttpClient } from '@angular/common/http';
import { computed, inject, Injectable, Signal, signal, WritableSignal } from '@angular/core';
import { catchError, map, Observable, Subscription, throwError } from 'rxjs';
import { Request, RequestFilters, RequestFiltersMap, RequestFromApi, RequestList } from '../objects/request';
import { mapHttpError } from '../app/utils/api';
import { environment } from '../environments/environment';
import { WorkRequestStatsFilterData, WorkRequestStatsFilters, WorkRequestStatsFiltersMap, WorkRequestStatsList } from '../objects/request-stats';

@Injectable({
  providedIn: 'root'
})
export class RequestStatsService {

  constructor(private http: HttpClient) {
  }

  loadRequestStats(filters: WorkRequestStatsFilters): Observable<WorkRequestStatsList> {
    return this.http.get<WorkRequestStatsList>(`${environment.apiHost}/api/work-request-stats`, {
      params: WorkRequestStatsFiltersMap(filters)
    })
      .pipe(
        catchError(error => {
          const errorString = mapHttpError(error);
          const submissionResult = {
            success: false,
            error: errorString
          };

          // Return an observable with a user-facing error message.
          return throwError(() => new Error(errorString));
        })
      )
  }

  loadRequestStatsFilterData(): Observable<WorkRequestStatsFilterData> {
    return this.http.get<WorkRequestStatsFilterData>(`${environment.apiHost}/api/work-request-stats/filter-data`)
      .pipe(
        catchError(error => {
          const errorString = mapHttpError(error);
          const submissionResult = {
            success: false,
            error: errorString
          };

          // Return an observable with a user-facing error message.
          return throwError(() => new Error(errorString));
        })
      )
  }
}
