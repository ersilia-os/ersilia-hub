import { Component, inject, OnInit, signal, Signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { RequestsListComponent } from './requests-list/requests-list.component';
import { NotificationsComponent } from './notifications/notifications.component';
import { AuthService } from '../services/auth.service';
import { LoginComponent } from './login/login.component';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { AuthType, User } from '../objects/auth';
import { Clipboard } from '@angular/cdk/clipboard';
import { NotificationsService, Notification } from './notifications/notifications.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RequestsListComponent, NotificationsComponent, LoginComponent, MatIconModule, MatMenuModule],
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

  constructor() {
    this.sessionDetails = this.authService.computeUserSessionSignal(session => {
      return {
        authed: session != null,
        sessionId: session == null ? undefined : session.session_id,
        authType: session == null ? undefined : session.auth_type
      };
    })
    this.user = this.authService.getUserSignal();
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
}

interface SessionDetails {
  authed: boolean;
  sessionId: string | undefined;
  authType: AuthType | undefined;
}