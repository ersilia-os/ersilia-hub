import { ActivatedRouteSnapshot, CanActivateFn, RouterStateSnapshot, Routes } from '@angular/router';
import { RequestsListComponent } from './requests-list/requests-list.component';
import { StatsComponent } from './stats/stats.component';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { ModelInstancesComponent } from './model-instances/model-instances.component';

export const routerGuardFunction: CanActivateFn = (
    next: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
) => {
    const authService = inject(AuthService);

    // TODO: when more permissions added -> check next state's link and match with permissions

    return authService.checkPermissions(['ADMIN']);
}

export const routes: Routes = [
    {
        path: '',
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
        path: '*',
        redirectTo: '',
    },
];

