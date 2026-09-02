
import type { Permission } from "./auth";

export interface User {
  id?: string;
  username: string;
  first_name: string;
  last_name: string;
  email?: string;
  sign_up_date?: Date;
  last_updated?: Date;
  /** Read-only, returned by the API. Written via updateUserPermissions(). */
  permissions?: Permission[];
}

export function mapUserFromApi(user: User): User {
  return {
    ...user,
    sign_up_date: user.sign_up_date ? new Date(user.sign_up_date) : undefined,
    last_updated: user.last_updated ? new Date(user.last_updated) : undefined,
    permissions: user.permissions ?? [],
  };
}

export function isAdmin(user: User): boolean {
  return user.permissions?.includes('ADMIN') === true;
}

export interface UsersFilter {
  username?: string;
  firstname_prefix?: string;
  lastname_prefix?: string;
  username_prefix?: string;
  email_prefix?: string;
}

export interface UserPasswordUpdate {
  new_password: string;
  current_password?: string;
  force: boolean;
}

export interface ForgotPasswordRequest {
  username: string;
  email: string;
}
