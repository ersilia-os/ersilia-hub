import { CommonModule } from '@angular/common';
import { Component, inject, Signal } from '@angular/core';
import { NotificationsService, Notification } from './notifications.service';
import { MatIconModule } from '@angular/material/icon';

@Component({
    standalone: true,
    imports: [
        CommonModule, MatIconModule
    ],
    templateUrl: './notifications.component.html',
    styleUrl: './notifications.component.scss',
    selector: 'notifications'
})
export class NotificationsComponent {
    private notificationsService = inject(NotificationsService);

    notifications: Signal<Notification[]>;

    constructor() {
        this.notifications = this.notificationsService.getNotificationsSignal();
    }

    removeNotification(id: string) {
        this.notificationsService.removeNotification(id);
    }
}