import { Component, inject, OnInit, signal, Signal, WritableSignal } from '@angular/core';
import { RequestsService, RequestSubmissionResult } from '../../../services/requests.service';
import { MatButtonModule } from '@angular/material/button';
import { RequestSubmission } from '../../../objects/request';
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
import { Model, ModelExecutionMode } from '../../../objects/model';
import { ModelsService, ModelSubmissionResult } from '../../../services/models.service';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { ErsiliaLoaderComponent } from '../../ersilia-loader/ersilia-loader.component';
import { NotificationsService, Notification } from '../../notifications/notifications.service';
import { AbstractControl, FormControl, FormGroupDirective, FormsModule, NgForm, ReactiveFormsModule, Validators } from "@angular/forms";
import { MatTooltipModule } from '@angular/material/tooltip';
import { ErrorStateMatcher } from '@angular/material/core';


@Component({
    standalone: true,
    imports: [
        MatButtonModule, CommonModule, MatIconModule, MatProgressBarModule,
        MatDialogActions, MatDialogClose, MatDialogTitle, MatDialogContent,
        MatFormFieldModule, MatSelectModule, FormsModule, MatInputModule, ErsiliaLoaderComponent,
        ReactiveFormsModule, MatTooltipModule
    ],
    templateUrl: './model-create.component.html',
    styleUrl: './model-create.component.scss'
})
export class ModelCreateComponent implements OnInit {
    readonly dialogRef = inject(MatDialogRef<ModelCreateComponent>);

    busy: WritableSignal<boolean> = signal(false);

    private modelsService = inject(ModelsService);
    private notificationsService = inject(NotificationsService);

    submitting: Signal<boolean>;
    submissionResult: ModelSubmissionResult | undefined;

    newModel: Model = Model();

    formControlErrorStateMatcher = new MyErrorStateMatcher()
    form: {
        modelId: FormControl;
        enabled: FormControl;
        description: FormControl;
        disableMemoryLimit: FormControl;
        maxInstances: FormControl;
        executionMode: FormControl;
        cpuRequest: FormControl;
        cpuLimit: FormControl;
        memoryRequest: FormControl;
        memoryLimit: FormControl;
    } = {
            modelId: new FormControl('eos', [
                Validators.required,
                (control) => validator(control, rawValue => {
                    if (rawValue == null || typeof rawValue !== 'string' || rawValue.length < 4 || !rawValue.startsWith('eos')) {
                        return {
                            'validation': 'Invalid Model Id'
                        }
                    }

                    return null;
                })
            ]),
            enabled: new FormControl(true, [
                Validators.required,
                (control) => validator(control, rawValue => {
                    if (rawValue == null || typeof rawValue !== 'boolean') {
                        return {
                            'validation': 'Invalid Enabled state'
                        }
                    }

                    return null;
                })
            ]),
            description: new FormControl('', [
                Validators.required,
                (control) => validator(control, rawValue => {
                    if (rawValue == null || typeof rawValue !== 'string' || rawValue.length < 5) {
                        return {
                            'validation': 'Invalid Description, need at least 5 charecters'
                        }
                    }

                    return null;
                })
            ]),
            disableMemoryLimit: new FormControl(false, [
                Validators.required,
                (control) => validator(control, rawValue => {
                    if (rawValue == null || typeof rawValue !== 'boolean') {
                        return {
                            'validation': 'Invalid Disable Memory Limit state'
                        }
                    }

                    return null;
                })
            ]),
            maxInstances: new FormControl(-1, [
                Validators.required,
                Validators.min(-1),
                Validators.max(30),
                (control) => validator(control, rawValue => {
                    if (rawValue == null || typeof rawValue !== 'number') {
                        return {
                            'validation': 'Invalid Max instances'
                        }
                    }

                    return null;
                })
            ]),
            executionMode: new FormControl(ModelExecutionMode.ASYNC, [
                Validators.required,
                (control) => validator(control, rawValue => {
                    if (rawValue == null || typeof rawValue !== 'string' || [ModelExecutionMode.ASYNC.toString(), ModelExecutionMode.SYNC.toString()].includes(rawValue)) {
                        return {
                            'validation': 'Invalid Execution Mode'
                        }
                    }

                    return null;
                })
            ]),
            cpuRequest: new FormControl(10, [
                Validators.required,
                Validators.min(10),
                Validators.max(1000),
                (control) => validator(control, rawValue => {
                    if (rawValue == null || typeof rawValue !== 'number') {
                        return {
                            'validation': 'Invalid CPU Request'
                        }
                    }

                    return null;
                })
            ]),
            cpuLimit: new FormControl(500, [
                Validators.required,
                Validators.min(50),
                Validators.max(5000),
                (control) => validator(control, rawValue => {
                    if (rawValue == null || typeof rawValue !== 'number') {
                        return {
                            'validation': 'Invalid CPU Limit'
                        }
                    }

                    return null;
                })
            ]),
            memoryRequest: new FormControl(100, [
                Validators.required,
                Validators.min(50),
                Validators.max(5000),
                (control) => validator(control, rawValue => {
                    if (rawValue == null || typeof rawValue !== 'number') {
                        return {
                            'validation': 'Invalid Memory Request'
                        }
                    }

                    return null;
                })
            ]),
            memoryLimit: new FormControl(3500, [
                Validators.required,
                Validators.min(100),
                Validators.max(15000),
                (control) => validator(control, rawValue => {
                    if (rawValue == null || typeof rawValue !== 'number') {
                        return {
                            'validation': 'Invalid Memory Limit'
                        }
                    }

                    return null;
                })
            ])
        };

    constructor() {
        this.submitting = this.modelsService.getModelSubmittingSignal();
    }

    ngOnInit() {
    }

    isSignUpFormValid(): boolean {
        return Object.values(this.form).every(control => control.valid);
    }

    clearForm() {
        Object.values(this.form).forEach(control => control.reset());
    }

    canSubmit() {
        return this.isSignUpFormValid();
    }

    submit() {
        if (!this.canSubmit()) {
            return;
        }

        this.busy.set(true);

        let model: Model = {
            id: this.form.modelId.getRawValue()!,
            enabled: this.form.enabled.getRawValue(),
            details: {
                template_version: "0.0.0",
                description: this.form.description.getRawValue(),
                disable_memory_limit: this.form.disableMemoryLimit.getRawValue(),
                max_instances: this.form.maxInstances.getRawValue(),
                execution_mode: this.form.executionMode.getRawValue(),
                k8s_resources: {
                    cpu_request: this.form.cpuRequest.getRawValue(),
                    cpu_limit: this.form.cpuLimit.getRawValue(),
                    memory_request: this.form.memoryRequest.getRawValue(),
                    memory_limit: this.form.memoryLimit.getRawValue()
                }
            }
        };

        this.modelsService.createModel(model)
            .subscribe({
                next: result => {
                    this.notificationsService.pushNotification(Notification('SUCCESS', 'Successfully Created Model!'));
                    this.close();
                },
                error: (err: Error) => {
                    if (err.message == 'Model already exists') {
                        this.form.modelId.setErrors({ 'validation': err.message });
                    }

                    this.notificationsService.pushNotification(Notification('ERROR', 'Model Creation Failed'));
                    this.busy.set(false);
                }
            });
    }

    close() {
        this.busy.set(false);
        this.clearForm();
        this.dialogRef.close();
    }
}

export class MyErrorStateMatcher implements ErrorStateMatcher {
    isErrorState(control: FormControl | null, form: FormGroupDirective | NgForm | null): boolean {
        const isSubmitted = form && form.submitted;
        return !!(control && control.invalid && (control.dirty || control.touched || isSubmitted));
    }
}

function validator(control: AbstractControl, validate: (rawValue: any) => { [id: string]: string } | null): { [id: string]: string } | null {
    if (!control.dirty) {
        return null;
    }

    const value = control.getRawValue();

    return validate(value);
}