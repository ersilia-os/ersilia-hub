import { computed, Injectable, Signal, signal, WritableSignal } from '@angular/core';
import { generateString } from '../utils/random';
import { timer } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class NotificationsService {

    private notifications: WritableSignal<Notification[]> = signal([]);
    private notificationTimeout = {
        'ERROR': 10000,
        'WARN': 8000,
        'INFO': 8000,
        'SUCCESS': 6000
    };

    constructor() {
        timer(0, 1000).subscribe({
            next: _ => {
                const currentTime = new Date().valueOf();
                const clearBefore = {
                    'ERROR': currentTime - this.notificationTimeout['ERROR'],
                    'WARN': currentTime - this.notificationTimeout['WARN'],
                    'INFO': currentTime - this.notificationTimeout['INFO'],
                    'SUCCESS': currentTime - this.notificationTimeout['SUCCESS'],
                };

                this.notifications.set(this.notifications()
                    .filter(notification =>
                        notification.creationTime > clearBefore[notification.type]
                    )
                )
            }
        });
    }

    getNotificationsSignal(): Signal<Notification[]> {
        return computed(() => this.notifications());
    }

    computeNotificationsSignal<T>(computation: (notifications: Notification[]) => T): Signal<T> {
        return computed(() => computation(this.notifications()));
    }

    pushNotification(notification: Notification) {
        this.notifications.set([notification, ...this.notifications()]);
    }

    removeNotification(id: string) {
        this.notifications.set(
            this.notifications().filter(notification => notification.id !== id)
        );
    }
}

export type NotificationType = 'ERROR' | 'WARN' | 'INFO' | 'SUCCESS';

export interface Notification {
    readonly id: string;
    readonly type: NotificationType;
    readonly message: string;
    readonly creationTime: number;
}

export function Notification(type: NotificationType, message: string): Notification {
    return {
        id: generateString(16),
        type: type,
        message: message,
        creationTime: new Date().valueOf()
    };
}