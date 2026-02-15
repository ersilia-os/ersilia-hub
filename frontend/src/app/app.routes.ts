import { ActivatedRouteSnapshot, CanActivateFn, Router, RouterStateSnapshot, Routes, UrlTree } from '@angular/router';
import { RequestsListComponent } from './requests-list/requests-list.component';
import { StatsComponent } from './stats/stats.component';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { ModelInstancesComponent } from './model-instances/model-instances.component';
import { ModelRecommendationsComponent } from './model-recommendations/model-recommendations.component';
import { ModelManagementComponent } from './model-management/model-management.component';
import { UserAdminComponent } from './user/admin/admin.component';
import { ModelReadonlyComponent } from './model-readonly/model-readonly.component';

export const routerGuardFunction: CanActivateFn = (
  next: ActivatedRouteSnapshot,
  state: RouterStateSnapshot
) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // TODO: when more permissions added -> check next state's link and match with permissions

  const hasPermission = authService.checkPermissions(['ADMIN']);

  const nextUrlPath = next.url.map(u => u.path).join("/");
  let nextUrlParams: string | undefined;

  if (Object.entries(next.queryParams).length > 0) {
    nextUrlParams = "?" + Object.entries(next.queryParams).map(param => `${param[0]}=${param[1]}`);
  }

  if (!hasPermission) {
    authService.setLoginRedirectUrl(nextUrlPath, nextUrlParams ?? '');
  }

  return hasPermission ?? router.parseUrl("/");
}

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'models'
  },
  {
    path: 'models',
    component: ModelReadonlyComponent,
  },
  {
    path: 'evaluations',
    component: RequestsListComponent,
  },
  {
    path: 'stats',
    component: StatsComponent,
    canActivate: [routerGuardFunction]
  },
  {
    path: 'instances',
    component: ModelInstancesComponent,
    canActivate: [routerGuardFunction]
  },
  {
    path: 'recommendations',
    component: ModelRecommendationsComponent,
    canActivate: [routerGuardFunction]
  },
  {
    path: 'models-admin',
    component: ModelManagementComponent,
    canActivate: [routerGuardFunction]
  },
  {
    path: 'users',
    component: UserAdminComponent,
    canActivate: [routerGuardFunction]
  },
  {
    path: '*',
    redirectTo: '',
  },
];

