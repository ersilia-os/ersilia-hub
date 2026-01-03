import { HttpClient, HttpErrorResponse, HttpHandlerFn, HttpRequest } from "@angular/common/http";
import { computed, inject, Injectable, Signal, signal, WritableSignal } from "@angular/core";
import { NotificationsService, Notification } from "../app/notifications/notifications.service";
import { AuthType, LoginResponse, mapUserSessionFromApi, Permission, userLoginAuth, UserSession } from "../objects/auth";
import { User, mapUserFromApi } from "../objects/user";
import { catchError, map, Observable, throwError, timer } from "rxjs";
import { mapHttpError } from "../app/utils/api";
import { environment } from "../environments/environment";


/**
 *
 * TODO: rethink session and auth relationship!
 *   - maybe start session on "login" and therefore also relate session age with login details (i.e. logout on session expire)
 *
 */

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private notificationService = inject(NotificationsService);

  readonly MAX_SESSION_AGE = 5 * 60 * 1000; // 5 minutes
  readonly SESSION_REFRESH_DELAY = 2 * 60 * 1000; // 2 minutes

  private user: WritableSignal<User | undefined> = signal(undefined);
  private userSession: WritableSignal<UserSession | undefined> = signal(undefined);
  private permissions: WritableSignal<Permission[]> = signal([]);
  private authType: WritableSignal<AuthType | undefined> = signal(undefined);
  private hasSession: WritableSignal<boolean> = signal(false);
  private lastAnonSessionId: WritableSignal<string | undefined> = signal(undefined);

  constructor(private http: HttpClient) {
    timer(0, this.SESSION_REFRESH_DELAY).subscribe(_ => {
      if (!this.hasSession()) {
        console.log("no session, no refresh");
        return;
      }

      this.refreshSession().subscribe();
    });

    timer(10000, this.SESSION_REFRESH_DELAY + 10000).subscribe(_ => {
      this.validateLocalSession();
    });
  }

  getLastAnonSessionId(): Signal<string | undefined> {
    return computed(() => this.lastAnonSessionId());
  }

  getUserSignal(): Signal<User | undefined> {
    return computed(() => this.user());
  }

  computeUserSignal<T>(computation: (user: User | undefined) => T): Signal<T> {
    return computed(() => computation(this.user()));
  }

  getUserSessionSignal(): Signal<UserSession | undefined> {
    return computed(() => this.userSession());
  }

  computeUserSessionSignal<T>(computation: (userSession: UserSession | undefined) => T): Signal<T> {
    return computed(() => computation(this.userSession()));
  }

  getAuthTypeSignal(): Signal<AuthType | undefined> {
    return computed(() => this.authType());
  }

  computeAuthTypeSignal<T>(computation: (authType: AuthType | undefined) => T): Signal<T> {
    return computed(() => computation(this.authType()));
  }

  getPermissionsSignal(): Signal<Permission[]> {
    return computed(() => this.permissions());
  }

  computePermissionsSignal<T>(computation: (user: Permission[]) => T): Signal<T> {
    return computed(() => computation(this.permissions()));
  }

  getAuthToken(): string | undefined {
    if (this.userSession == null || this.userSession() == null) {
      return undefined;
    }

    return btoa(JSON.stringify(this.userSession()));
  }

  getAuthType(): string | undefined {
    if (this.authType == null || this.authType() == null) {
      return undefined;
    }

    return this.authType();
  }

  checkPermissions(one_of: (Permission | string)[]): boolean {
    return hasPermission(this.permissions(), one_of);
  }

  init() {
    this.loadFromCache();
    this.validateLocalSession();
  }

  private clearSession() {
    console.log("clearing cache...");

    localStorage.removeItem("session");
    this.userSession.set(undefined);

    localStorage.removeItem("user");
    this.user.set(undefined);

    localStorage.removeItem("permissions");
    this.permissions.set([]);

    this.hasSession.set(false);
  }

  private updateCache() {
    let sessionCached = false;

    if (this.userSession != null && this.userSession() != null) {
      localStorage.setItem("session", btoa(JSON.stringify(this.userSession())));
      sessionCached = true;
    }

    if (this.user != null && this.user() != null) {
      localStorage.setItem("user", btoa(JSON.stringify(this.user())));
    }

    if (this.permissions != null) {
      localStorage.setItem("permissions", btoa(this.permissions().join(",")))
    }

    if (this.authType != null && this.authType() != null) {
      localStorage.setItem("authType", this.authType()!);

      if (this.authType() === 'ErsiliaAnonymous' && sessionCached) {
        localStorage.setItem("lastAnonSessionId", this.userSession()!.session_id);
      }
    }
  }

  private loadFromCache() {
    this.lastAnonSessionId.set(localStorage.getItem("lastAnonSessionId") ?? undefined);

    const session = localStorage.getItem("session");

    if (session == null || session.length < 10) {
      this.clearSession();

      return;
    }

    try {
      this.userSession.set(mapUserSessionFromApi(JSON.parse(atob(session))));
      this.hasSession.set(true);
    } catch (e) {
      console.error("Failed to load session from cache");
      this.clearSession();
    }

    const authType = localStorage.getItem("authType");
    this.authType.set(authType as AuthType | undefined);

    const permissions = localStorage.getItem("permissions");

    if (permissions == null || permissions.length < 3) {
      this.permissions.set([]);
    } else {
      try {
        this.permissions.set(atob(permissions).split(",") as Permission[]);
      } catch (e) {
        console.error("Failed to load Permissions from cache");
      }
    }

    const user = localStorage.getItem("user");

    if (user == null || user.length < 10) {
      // TODO: reload user ?
      this.user.set(undefined);

      return
    } else {
      try {
        this.user.set(mapUserFromApi(JSON.parse(atob(user))));
      } catch (e) {
        console.error("Failed to load user from cache");
      }
    }
  }

  signup(user: User, password: string): Observable<User> {
    return this.http.post<User>(`${environment.apiHost}/api/auth/signup`, {
      user: user,
      password: password
    })
      .pipe(
        map(response => {
          return response;
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }

  userLogin(username: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${environment.apiHost}/api/auth/login`, userLoginAuth(username, password))
      .pipe(
        map(response => {
          this.user.set(mapUserFromApi(response.user));
          this.userSession.set(mapUserSessionFromApi(response.session));
          this.permissions.set(response.permissions);
          this.updateCache();
          this.hasSession.set(true);
          this.authType.set(response.session.auth_type);

          return response;
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }

  logout(): Observable<boolean> {
    return this.http.post(`${environment.apiHost}/api/auth/logout`, undefined)
      .pipe(
        map(response => {
          this.clearSession();

          return true;
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }

  anonLogin(sessionId: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${environment.apiHost}/api/auth/anonymous-login/${sessionId}`, null)
      .pipe(
        map(response => {
          this.user.set(mapUserFromApi(response.user));
          this.userSession.set(mapUserSessionFromApi(response.session));
          this.lastAnonSessionId.set(sessionId);
          this.updateCache();
          this.hasSession.set(true);
          this.authType.set(response.session.auth_type);

          return response;
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }

  private refreshSession() {
    return this.http.post<UserSession>(`${environment.apiHost}/api/auth/session/refresh`, undefined)
      .pipe(
        map(response => {
          this.userSession.set(response);
          this.updateCache();
          this.hasSession.set(true);

          return true;
        }),
        catchError((error: HttpErrorResponse) => {
          if (error.status == 400 || error.status == 401) {
            this.clearSession();
          }

          return throwError(() => new Error(mapHttpError(error)));
        })
      );
  }

  private validateLocalSession() {
    if (this.userSession == null || this.userSession() == null || this.userSession()?.session_start_time == null) {
      this.clearSession();
      return;
    }

    const dateNow = new Date();

    console.log(`session_start_time [${this.userSession()!.session_start_time}] = [${this.userSession()!.session_start_time.valueOf()}]`);
    console.log(`dateNow [${dateNow}] = [${dateNow.valueOf()}]`);
    console.log("session_max_age_seconds =", this.userSession()!.session_max_age_seconds);
    console.log("check =", (this.userSession()!.session_start_time.valueOf() + (this.userSession()!.session_max_age_seconds * 1000) <= dateNow.valueOf()));

    if (this.userSession()!.session_start_time.valueOf() + (this.userSession()!.session_max_age_seconds * 1000) <= dateNow.valueOf()) {
      this.notificationService.pushNotification(Notification('INFO', 'User session has expired'));
      this.clearSession();
      return;
    }

    this.hasSession.set(true);
  }
}

export function authInterceptor(req: HttpRequest<unknown>, next: HttpHandlerFn) {
  const authService = inject(AuthService);
  let newHeaders = req.headers;

  const authType = authService.getAuthType();
  const authToken = authService.getAuthToken();

  if (authType != null && authToken != null) {
    newHeaders = newHeaders.append('Authorization', `${authType} ${authToken}`)
  }

  const newReq = req.clone({
    headers: newHeaders,
  });

  return next(newReq);
}

export function hasPermission(permissions: Permission[], one_of: (Permission | string)[]): boolean {
  return one_of.some(p => permissions.includes(p as Permission));
}
