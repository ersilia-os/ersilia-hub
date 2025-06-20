import { Component, inject, OnInit, signal, Signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { RequestsListComponent } from './requests-list/requests-list.component';
import { NotificationsComponent } from './notifications/notifications.component';
import { AuthService, hasPermission } from '../services/auth.service';
import { LoginComponent } from './login/login.component';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { AppPermissions, AuthType, EmptyPermissions, User } from '../objects/auth';
import { Clipboard } from '@angular/cdk/clipboard';
import { NotificationsService, Notification } from './notifications/notifications.service';
import { MenuComponent } from './menu/menu.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet, RequestsListComponent,
    NotificationsComponent, LoginComponent,
    MatIconModule, MatMenuModule, MenuComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  title = 'ersilia-hub';

  private authService = inject(AuthService);
  private clipboard = inject(Clipboard);
  private notificationsService = inject(NotificationsService);

  sessionDetails: Signal<SessionDetails>;
  user: Signal<User | undefined>;
  appPermissions: Signal<AppPermissions> = signal(EmptyPermissions());

  menuExpanded: boolean = false;

  constructor() {
    this.sessionDetails = this.authService.computeUserSessionSignal(session => {
      return {
        authed: session != null,
        sessionId: session == null ? undefined : session.session_id,
        authType: session == null ? undefined : session.auth_type
      };
    })
    this.user = this.authService.getUserSignal();
    this.appPermissions = this.authService.computePermissionsSignal(p => {
      return {
        canViewMenu: hasPermission(p, ["ADMIN"]),
        canViewStats: hasPermission(p, ["ADMIN"]),
        canManageRequests: hasPermission(p, ["ADMIN"]),
        canManageInstances: hasPermission(p, ["ADMIN"])
      }
    });
  }

  ngOnInit() {
    this.authService.init();
  }

  logout() {
    this.authService.logout().subscribe();
  }

  copyAnonSessionId() {
    if (this.sessionDetails == null || !this.sessionDetails().authed || this.sessionDetails().authType !== 'ErsiliaAnonymous') {
      return;
    }

    if (this.clipboard.copy(this.sessionDetails().sessionId!)) {
      this.notificationsService.pushNotification(Notification('SUCCESS', 'Session Id Copied'))
    } else {
      this.notificationsService.pushNotification(Notification('WARN', 'Failed to copy Session Id'))
    }
  }

  toggleMenu() {
    this.menuExpanded = !this.menuExpanded;
  }
}

interface SessionDetails {
  authed: boolean;
  sessionId: string | undefined;
  authType: AuthType | undefined;
}
