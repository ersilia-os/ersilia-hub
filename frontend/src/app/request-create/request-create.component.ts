import { Component, computed, inject, OnInit, signal, Signal, WritableSignal } from '@angular/core';
import { RequestsService, RequestSubmissionResult } from '../../services/requests.service';
import { MatButtonModule } from '@angular/material/button';
import { RequestSubmission } from '../../objects/request';
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
import { filterModels, Model, ModelFilter } from '../../objects/model';
import { ModelsService } from '../../services/models.service';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { FormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { ErsiliaLoaderComponent } from '../ersilia-loader/ersilia-loader.component';
import { NotificationsService, Notification } from '../notifications/notifications.service';
import { AuthService } from '../../services/auth.service';
import { MatCheckboxModule } from '@angular/material/checkbox';


@Component({
  standalone: true,
  imports: [
    MatButtonModule, CommonModule, MatIconModule, MatProgressBarModule,
    MatDialogActions, MatDialogClose, MatDialogTitle, MatDialogContent,
    MatFormFieldModule, MatSelectModule, FormsModule, MatInputModule, ErsiliaLoaderComponent,
    MatCheckboxModule
  ],
  templateUrl: './request-create.component.html',
  styleUrl: './request-create.component.scss'
})
export class RequestsCreateComponent implements OnInit {
  readonly dialogRef = inject(MatDialogRef<RequestsCreateComponent>);
  readonly dialogData = inject(MAT_DIALOG_DATA);

  private requestService = inject(RequestsService);
  private modelsService = inject(ModelsService);
  private notificationsService = inject(NotificationsService);
  private auth = inject(AuthService);

  userCanContributeToCache: boolean = false;
  models: Signal<Model[]>;
  filteredModels: Signal<Model[]>;
  filters: WritableSignal<ModelFilter> = signal({ freeText: undefined, id: undefined, description: undefined });
  modelsLoading: Signal<boolean>;

  modelSelectionDisabled: boolean = false;

  private _selectedModel: string | undefined;

  get selectedModel() {
    return this._selectedModel;
  }

  set selectedModel(value: string | undefined) {
    this._selectedModel = value;

    if (value == null || !this.userCanContributeToCache) {
      this.canOptInToCache.set(false);

      return;
    }

    let model = this.models().find(m => m.id === value);
    this.canOptInToCache.set(model != null && model.details.cache_enabled);
  }

  get filterFreeText(): string | undefined {
    return this.filters().freeText;
  }

  set filterFreeText(value: string | undefined) {
    this.filters.set({ ...this.filters(), freeText: value });
  }

  get filterId(): string | undefined {
    return this.filters().id;
  }

  set filterId(value: string | undefined) {
    this.filters.set({ ...this.filters(), id: value });
  }

  get filterDescription(): string | undefined {
    return this.filters().description;
  }

  set filterDescription(value: string | undefined) {
    this.filters.set({ ...this.filters(), description: value });
  }

  fileName: string | undefined;

  private _entriesString: string = ""
  private entries: string[] = [];

  get entriesString(): string {
    return this._entriesString;
  }

  set entriesString(entriesString: string) {
    this.entries = mapEntriesString(entriesString);
  }

  private _cacheOptIn: boolean = false;

  get cacheOptIn(): boolean {
    return this._cacheOptIn;
  }

  set cacheOptIn(value: boolean) {
    this._cacheOptIn = value;
  }

  submitting: Signal<boolean>;
  submissionResult: RequestSubmissionResult | undefined;
  canOptInToCache: WritableSignal<boolean> = signal(false);

  constructor() {
    this.models = this.modelsService.computeModelsSignal(models => models.filter(m => m.enabled));
    this.modelsLoading = this.modelsService.computeModelsLoadingSignal(_loading => {
      return this.models == null || _loading
    });
    this.filteredModels = computed(() => filterModels(this.models(), this.filters()));
    this.submitting = this.requestService.getRequestSubmittingSignal();
    this.userCanContributeToCache = this.auth.getAuthType() === 'ErsiliaUser';
  }

  ngOnInit() {
    this.refreshModels();

    if (this.dialogData != null && this.dialogData.id != null) {
      this.selectedModel = this.dialogData.id;
      this.modelSelectionDisabled = true;
    }
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

    this.requestService.submitRequest(RequestSubmission(this.selectedModel!, this.entries, this.cacheOptIn))
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
