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

export interface User {
    id?: string;
    username: string;
    first_name: string;
    last_name: string;
    email?: string;
    sign_up_date?: Date;
    last_updated?: Date;
}

export function mapUserFromApi(user: User): User {
    return {
        ...user,
        sign_up_date: user.sign_up_date ? new Date(user.sign_up_date) : undefined,
        last_updated: user.last_updated ? new Date(user.last_updated) : undefined,
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
}

export function EmptyPermissions(): AppPermissions {
    return {
        canViewMenu: false,
        canViewStats: false,
        canManageRequests: false,
        canManageInstances: false
    };
}