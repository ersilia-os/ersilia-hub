import { User } from "./user";

export interface UserSession {
  userid: string;
  session_id: string;
  session_token: string;
  auth_type: AuthType;
  session_max_age_seconds: number;
  session_start_time: Date;
}

export function mapUserSessionFromApi(userSession: UserSession): UserSession {
  return {
    ...userSession,
    session_start_time: new Date(userSession.session_start_time)
  };
}

export interface UserSignUp {
  user: User
  password: string;
}

export type AuthType = 'ErsiliaAnonymous' | 'ErsiliaUser';

// login
export interface EncodedAuth {
  encoding: string;
  auth_type: AuthType
}

export function userLoginAuth(username: string, password: string): EncodedAuth {
  return {
    encoding: btoa(`${username}:${password}`),
    auth_type: 'ErsiliaUser'
  }
}

export type Permission = 'ADMIN';

export interface LoginResponse {
  user: User;
  session: UserSession;
  permissions: Permission[];
}

export interface AppPermissions {
  canViewMenu: boolean;
  canViewStats: boolean;
  canManageRequests: boolean;
  canManageInstances: boolean;
  canManageUsers: boolean;
}

export function EmptyPermissions(): AppPermissions {
  return {
    canViewMenu: false,
    canViewStats: false,
    canManageRequests: false,
    canManageInstances: false,
    canManageUsers: false
  };
}

export interface UserPermissionsUpdate {
  permissions: Permission[];
}
