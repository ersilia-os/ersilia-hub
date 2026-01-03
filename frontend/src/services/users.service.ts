import { HttpClient, HttpErrorResponse, HttpHandlerFn, HttpRequest } from "@angular/common/http";
import { computed, inject, Injectable, Signal, signal, WritableSignal } from "@angular/core";
import { NotificationsService, Notification } from "../app/notifications/notifications.service";
import { AuthType, LoginResponse, mapUserSessionFromApi, Permission, userLoginAuth, UserSession } from "../objects/auth";
import { catchError, map, Observable, throwError, timer } from "rxjs";
import { mapHttpError } from "../app/utils/api";
import { environment } from "../environments/environment";
import { User, UsersFilter, mapUserFromApi } from "../objects/user";
import { APIFiltersMap, APIList } from "../objects/common";


/**
 *
 * TODO: rethink session and auth relationship!
 *   - maybe start session on "login" and therefore also relate session age with login details (i.e. logout on session expire)
 *
 */

@Injectable({
  providedIn: 'root'
})
export class UsersService {

  constructor(private http: HttpClient) {
  }

  loadUser(userId: string): Observable<User> {
    return this.http.get<User>(`${environment.apiHost}/api/users/${userId}`)
      .pipe(
        map(response => {
          return mapUserFromApi(response);
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }

  filterUsers(filter: UsersFilter): Observable<User[]> {
    return this.http.get<APIList<User>>(`${environment.apiHost}/api/users`, { params: APIFiltersMap(filter) })
      .pipe(
        map(response => {
          return response.items.map(mapUserFromApi);
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }

  clearUserContributions(userId: string): Observable<void> {
    return this.http.delete(`${environment.apiHost}/api/users/${userId}/contributions`)
      .pipe(
        map(response => {
          return;
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }

  clearUserData(userId: string): Observable<void> {
    return this.http.delete(`${environment.apiHost}/api/users/${userId}/data`)
      .pipe(
        map(response => {
          return;
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }

  deleteUser(userId: string): Observable<void> {
    return this.http.delete(`${environment.apiHost}/api/users/${userId}`)
      .pipe(
        map(response => {
          return;
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }

  updateUserPermissions(userId: string, permissions: Permission[]): Observable<void> {
    return this.http.put(`${environment.apiHost}/api/users/${userId}/permissions`, { permissions: permissions })
      .pipe(
        map(response => {
          return;
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }

  updateUserPassword(userId: string, newPassword: string, currentPassword?: string, force?: boolean): Observable<void> {
    return this.http.put(`${environment.apiHost}/api/users/${userId}/password`, {
      new_password: newPassword,
      current_password: currentPassword,
      force: force,
    })
      .pipe(
        map(response => {
          return;
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }
}
