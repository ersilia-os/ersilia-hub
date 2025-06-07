import { Component, inject, OnInit, Signal } from '@angular/core';
import { RequestsService, RequestSubmissionResult } from '../../services/requests.service';
import { MatButtonModule } from '@angular/material/button';
import { RequestSubmission } from '../../objects/request';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import {
    MatDialogActions,
    MatDialogClose,
    MatDialogContent,
    MatDialogRef,
    MatDialogTitle,
} from '@angular/material/dialog';
import { Model } from '../../objects/model';
import { ModelsService } from '../../services/models.service';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { FormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { ErsiliaLoaderComponent } from '../ersilia-loader/ersilia-loader.component';
import { NotificationsService, Notification } from '../notifications/notifications.service';


@Component({
    standalone: true,
    imports: [
        MatButtonModule, CommonModule, MatIconModule, MatProgressBarModule,
        MatDialogActions, MatDialogClose, MatDialogTitle, MatDialogContent,
        MatFormFieldModule, MatSelectModule, FormsModule, MatInputModule, ErsiliaLoaderComponent
    ],
    templateUrl: './request-create.component.html',
    styleUrl: './request-create.component.scss'
})
export class RequestsCreateComponent implements OnInit {
    readonly dialogRef = inject(MatDialogRef<RequestsCreateComponent>);

    private requestService = inject(RequestsService);
    private modelsService = inject(ModelsService);
    private notificationsService = inject(NotificationsService);

    models: Signal<Model[]>
    modelsLoading: Signal<boolean>;
    selectedModel: string | undefined;
    fileName: string | undefined;

    private _entriesString: string = ""
    private entries: string[] = [];

    get entriesString(): string {
        return this._entriesString;
    }

    set entriesString(entriesString: string) {
        this.entries = mapEntriesString(entriesString);
    }

    submitting: Signal<boolean>;
    submissionResult: RequestSubmissionResult | undefined;

    constructor() {
        this.models = this.modelsService.getModelsSignal();
        this.modelsLoading = this.modelsService.computeModelsLoadingSignal(_loading => {
            return this.models == null || _loading
        });
        this.submitting = this.requestService.getRequestSubmittingSignal();
    }

    ngOnInit() {
        this.refreshModels();
    }

    refreshModels() {
        this.modelsService.loadModels();
    }

    close() {
        this.dialogRef.close();
    }

    canSubmit(): boolean {
        return (this.selectedModel != null && this.selectedModel?.length > 0)
            && (this.entries != null && this.entries.length > 0)
            && !this.submitting();
    }

    submit() {
        if (!this.canSubmit()) {
            return;
        }

        this.requestService.submitRequest(RequestSubmission(this.selectedModel!, this.entries))
            .subscribe({
                next: result => {
                    this.submissionResult = result;
                    this.notificationsService.pushNotification(Notification('SUCCESS', `Evaluation submitted for model ${this.selectedModel!}`));
                    this.close();
                },
                error: err => {
                    this.notificationsService.pushNotification(Notification('ERROR', `Failed to submit evaluation for model ${this.selectedModel!}`));
                }
            });

        /*
CC(C)CC1=CC=C(C=C1)C(C)C(=O)O
CC1(OC2C(OC(C2O1)(C#N)C3=CC=C4N3N=CN=C4N)CO)C
COC1=CC23CCCN2CCC4=CC5=C(C=C4C3C1O)OCO5
        */
    }

    onFileSelected(event: any) {
        const file: File = event.target.files[0];

        if (file) {
            this.fileName = file.name;

            try {
                const fileReader = new FileReader();
                fileReader.onload = (e: any) => {
                    this._entriesString = e.target.result;
                    this.entries = mapEntriesString(this._entriesString)
                };
                fileReader.readAsText(file);
            } catch (e) {
                this.notificationsService.pushNotification(Notification('WARN', 'Failed to read input file'));
                console.error("failed to read input file: ", e);
            }
        }
    }
}

function mapEntriesString(entriesString: string | undefined): string[] {
    if (entriesString == null || entriesString.length == 0) {
        return [];
    } else {
        return entriesString.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
    }
}