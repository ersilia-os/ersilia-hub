import { Component, inject, OnInit, signal, Signal, WritableSignal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
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
import { AbstractControl, Form, FormControl, FormGroupDirective, FormsModule, NgForm, ReactiveFormsModule, Validators } from "@angular/forms";
import { MatTooltipModule } from '@angular/material/tooltip';
import { ErrorStateMatcher } from '@angular/material/core';
import { MatCheckboxModule } from '@angular/material/checkbox';

@Component({
  standalone: true,
  imports: [
    MatButtonModule, CommonModule, MatIconModule, MatProgressBarModule,
    MatDialogActions, MatDialogClose, MatDialogTitle, MatDialogContent,
    MatFormFieldModule, MatSelectModule, FormsModule, MatInputModule, ErsiliaLoaderComponent,
    ReactiveFormsModule, MatTooltipModule, MatCheckboxModule
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
  importing: WritableSignal<boolean> = signal(false);

  formControlErrorStateMatcher = new MyErrorStateMatcher()
  form: {
    modelId: FormControl;
    enabled: FormControl;
    disableMemoryLimit: FormControl;
    maxInstances: FormControl;
    executionMode: FormControl;
    cpuRequest: FormControl;
    cpuLimit: FormControl;
    memoryRequest: FormControl;
    memoryLimit: FormControl;
    imageTag: FormControl;
    cacheEnabled: FormControl;

    // identification details
    description: FormControl;
    title: FormControl;
    interpretation: FormControl;
    slug: FormControl;
    source_code: FormControl;
    publication: FormControl;
    target_organisms: FormControl;
    biomedical_areas: FormControl;
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
          if (rawValue == null || typeof rawValue !== 'string' || ![ModelExecutionMode.ASYNC.toString(), ModelExecutionMode.SYNC.toString()].includes(rawValue)) {
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
      ]),
      imageTag: new FormControl('latest', [
        Validators.required,
        (control) => validator(control, rawValue => {
          if (rawValue == null || typeof rawValue !== 'string' || rawValue.length < 4) {
            return {
              'validation': 'Invalid Image Tag, need at least 4 charecters'
            }
          }

          return null;
        })
      ]),
      cacheEnabled: new FormControl(false, [
        Validators.required,
        (control) => validator(control, rawValue => {
          if (rawValue == null || typeof rawValue !== 'boolean') {
            return {
              'validation': 'Invalid Cache Enabled State'
            }
          }

          return null;
        })
      ]),

      // identification details
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
      title: new FormControl('', [
        (control) => validator(control, rawValue => {
          if (rawValue == null || typeof rawValue !== 'string' || rawValue.length < 3) {
            return {
              'validation': 'Invalid title, need at least 3 charecters'
            }
          }

          return null;
        })
      ]),
      slug: new FormControl('', [
        (control) => validator(control, rawValue => {
          if (rawValue == null || typeof rawValue !== 'string' || rawValue.length < 3) {
            return {
              'validation': 'Invalid slug, need at least 3 charecters'
            }
          }

          return null;
        })
      ]),
      interpretation: new FormControl('', [
        (control) => validator(control, rawValue => {
          if (rawValue == null || typeof rawValue !== 'string' || rawValue.length < 3) {
            return {
              'validation': 'Invalid interpretation, need at least 3 charecters'
            }
          }

          return null;
        })
      ]),
      source_code: new FormControl('', [
        (control) => validator(control, rawValue => {
          if (rawValue == null || typeof rawValue !== 'string' || rawValue.length < 3) {
            return {
              'validation': 'Invalid source_code, need at least 3 charecters'
            }
          }

          return null;
        })
      ]),
      publication: new FormControl('', [
        (control) => validator(control, rawValue => {
          if (rawValue == null || typeof rawValue !== 'string' || rawValue.length < 3) {
            return {
              'validation': 'Invalid publication, need at least 3 charecters'
            }
          }

          return null;
        })
      ]),
      target_organisms: new FormControl('', [
        (control) => validator(control, rawValue => {
          if (rawValue == null || typeof rawValue !== 'string' || rawValue.length < 5) {
            return {
              'validation': 'Invalid target organisms, need at least 5 charecters'
            }
          }

          return null;
        })
      ]),
      biomedical_areas: new FormControl('', [
        (control) => validator(control, rawValue => {
          if (rawValue == null || typeof rawValue !== 'string' || rawValue.length < 5) {
            return {
              'validation': 'Invalid biomedical areas, need at least 5 charecters'
            }
          }

          return null;
        })
      ]),
    };

  get formModelEnabled(): boolean {
    const val = this.form.enabled.getRawValue();
    return typeof val === 'boolean' ? val : false;
  }

  set formModelEnabled(value: boolean) {
    this.form.enabled.setValue(value);
  }

  get formDisableMemoryLimit(): boolean {
    const val = this.form.disableMemoryLimit.getRawValue();
    return typeof val === 'boolean' ? val : false;
  }

  set formDisableMemoryLimit(value: boolean) {
    this.form.disableMemoryLimit.setValue(value);
  }

  get formCacheEnabled(): boolean {
    const val = this.form.cacheEnabled.getRawValue();
    return typeof val === 'boolean' ? val : false;
  }

  set formCacheEnabled(value: boolean) {
    this.form.cacheEnabled.setValue(value);
  }

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
        },
        image_tag: this.form.imageTag.getRawValue(),
        cache_enabled: this.form.cacheEnabled.getRawValue(),
        identification_details: {
          description: this.form.description.getRawValue(),
          title: this.form.title.getRawValue(),
          slug: this.form.slug.getRawValue(),
          interpretation: this.form.interpretation.getRawValue(),
          publication: this.form.publication.getRawValue(),
          source_code: this.form.source_code.getRawValue(),
          target_organisms: this.form.target_organisms.getRawValue() == null ? undefined : this.form.target_organisms.getRawValue().split(","),
          biomedical_areas: this.form.biomedical_areas.getRawValue() == null ? undefined : this.form.biomedical_areas.getRawValue().split(","),
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
          if (err.message.includes('already exists')) {
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

  importIdentificationDetails() {
    if (this.importing()) {
      return;
    }

    this.importing.set(true);

    this.modelsService.getIdentificationDetails(this.form.modelId.getRawValue()).subscribe({
      next: details => {
        this.form.description.setValue(details.description);
        this.form.title.setValue(details.title);
        this.form.slug.setValue(details.slug);
        this.form.interpretation.setValue(details.interpretation);
        this.form.source_code.setValue(details.source_code);
        this.form.publication.setValue(details.publication);

        if (details.target_organisms != undefined) {
          this.form.target_organisms.setValue(details.target_organisms.join(","));
        }

        if (details.biomedical_areas != undefined) {
          this.form.biomedical_areas.setValue(details.biomedical_areas.join(","));
        }

        this.importing.set(false);
      },
      error: err => {
        this.notificationsService.pushNotification(Notification("WARN", "Failed to import details from ModelHub"));
        this.importing.set(false);
      }
    })
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
