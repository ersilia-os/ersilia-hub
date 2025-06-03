import { Component, inject, OnInit, signal, WritableSignal } from '@angular/core';
import { RequestsService } from '../../services/requests.service';
import { MatButtonModule } from '@angular/material/button';
import { RequestStatus } from '../../objects/request';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import {
    MAT_DIALOG_DATA,
    MatDialogActions,
    MatDialogClose,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle,
} from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { FormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { ErsiliaLoaderComponent } from '../ersilia-loader/ersilia-loader.component';
import { mapRequest, RequestDisplay } from '../../objects/request-view';
import { NotificationsService, Notification } from '../notifications/notifications.service';
import { Observable, Subscription, timer } from 'rxjs';


@Component({
    standalone: true,
    imports: [
        MatButtonModule, CommonModule, MatIconModule, MatProgressBarModule,
        MatDialogActions, MatDialogClose, MatDialogTitle, MatDialogContent,
        MatFormFieldModule, MatSelectModule, FormsModule, MatInputModule, ErsiliaLoaderComponent
    ],
    templateUrl: './request-view.component.html',
    styleUrl: './request-view.component.scss'
})
export class RequestViewComponent implements OnInit {
    private notificationService = inject(NotificationsService);

    readonly dialogRef = inject(MatDialogRef<RequestViewComponent>);
    readonly requestData: RequestDisplay = inject(MAT_DIALOG_DATA);

    private requestService = inject(RequestsService);

    loading: WritableSignal<boolean> = signal(true);
    downloadingResult: WritableSignal<boolean> = signal(false);
    request: WritableSignal<RequestDisplay | undefined> = signal(undefined);

    private timer$: Observable<number> | undefined;
    private timerSubscription: Subscription | undefined;

    constructor() {
    }

    ngOnInit() {
        if (this.request() == undefined) {
            this.request.set(this.requestData);
        }

        if (this.request()?.request_status == RequestStatus.COMPLETED || this.request()?.request_status == RequestStatus.FAILED) {
            this.loading.set(false);
            return;
        }

        this.timer$ = timer(2000, 3000);
        this.timerSubscription = this.timer$.subscribe({
            next: _ => {
                this.load();
            }
        });

        this.loading.set(false);
    }

    private deleteRefreshTimer() {
        if (this.timerSubscription != null) {
            this.timerSubscription.unsubscribe();
            this.timer$ = undefined;
        }
    }

    load(download_result?: boolean) {
        if (!download_result && this.loading()) {
            return;
        } else if (download_result && this.downloadingResult()) {
            return;
        }

        if (!download_result) {
            this.loading.set(true);
        } else {
            this.downloadingResult.set(true);
        }

        this.requestService.loadRequest(this.requestData.id!, download_result)
            .subscribe({
                next: result => {
                    this.request.set(mapRequest(result));

                    if (download_result) {
                        if (this.request()?.has_result && result.result != null) {
                            const a = document.createElement('a');
                            const objectUrl = URL.createObjectURL(new Blob([JSON.stringify(result.result, null, 2)], {
                                type: "application/json",
                            }));
                            a.href = objectUrl;
                            a.download = `ersiliahub_${this.request()?.model_id}_${this.request()?.id}.json`;
                            a.click();
                            URL.revokeObjectURL(objectUrl);
                        } else {
                            this.notificationService.pushNotification(Notification('WARN', 'Failed to download result. Please try again'));
                        }

                        this.downloadingResult.set(false);
                    } else {
                        this.loading.set(false);

                        if (this.request()?.request_status == RequestStatus.COMPLETED || this.request()?.request_status == RequestStatus.FAILED) {
                            this.deleteRefreshTimer();
                        }
                    }
                },
                error: err => {
                    if (!download_result) {
                        this.notificationService.pushNotification(Notification('ERROR', `Failed to refresh`));
                        this.loading.set(false);
                    } else {
                        this.notificationService.pushNotification(Notification('ERROR', `Failed to download result`));
                        this.downloadingResult.set(false);
                    }
                }
            })
    }

    close() {
        this.deleteRefreshTimer();
        this.dialogRef.close();
    }

    canDownloadResult(): boolean {
        return this.request != undefined
            && this.request()!.has_result
            && !this.downloadingResult();
    }

    downloadResult() {
        if (!this.canDownloadResult()) {
            console.log("cannot download result")
            return;
        }

        this.load(true);
    }
}
