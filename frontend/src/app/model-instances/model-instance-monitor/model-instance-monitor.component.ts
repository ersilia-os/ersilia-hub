
import { Component, inject, OnDestroy, OnInit, signal, Signal, TrackByFunction, WritableSignal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
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
import { ErsiliaLoaderComponent } from '../../ersilia-loader/ersilia-loader.component';
import { NotificationsService, Notification } from '../../notifications/notifications.service';
import { ExtendedModelInstance, InstanceLogEntry, JobLogsFilters, ModelInstanceFilters, ModelInstanceState } from '../../../objects/instance';
import { Subscription, timer } from 'rxjs';
import { ModelsService } from '../../../services/models.service';
import { InstancesService } from '../../../services/instances.service';
import { ModelInstanceResourceComponent } from '../../model-instance-resource/model-instance-resource.component';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTableModule } from '@angular/material/table';
import { K8sPod } from '../../../objects/k8s';
import { MatSelectModule } from '@angular/material/select';

@Component({
  standalone: true,
  imports: [
    MatButtonModule, CommonModule, MatIconModule, MatProgressBarModule,
    MatDialogActions, MatDialogClose, MatDialogTitle, MatDialogContent,
    MatExpansionModule, MatTableModule, MatSelectModule,
    MatFormFieldModule, ErsiliaLoaderComponent,
    ModelInstanceResourceComponent
  ],
  templateUrl: './model-instance-monitor.component.html',
  styleUrl: './model-instance-monitor.component.scss'
})
export class ModelInstanceMonitorComponent implements OnDestroy {
  readonly instanceHistoryDisplayedColumns: string[] = ['log_event', 'log_timestamp', 'instance_details'];
  readonly instanceHistoryColumnHeaders: { [column: string]: string } = {
    log_event: 'Event',
    log_timestamp: 'Timestamp',
    instance_details: 'Instance Details'
  };

  readonly dialogRef = inject(MatDialogRef<ModelInstanceMonitorComponent>);
  readonly dialogData = inject(MAT_DIALOG_DATA);

  private instancesService = inject(InstancesService);
  instance: WritableSignal<ExtendedModelInstance>;
  private instanceFilters: ModelInstanceFilters = {
    load_resource_profiles: true,
    load_recommendations: true
  };
  jobLogs: WritableSignal<string[]> = signal([]);
  private jobLogsFilters: JobLogsFilters = {
    tail: 50
  }
  history: WritableSignal<InstanceLogEntry[]> = signal([]);

  private instanceRefreshTimer$: Subscription | undefined;
  private jobLogsRefreshTimer$: Subscription | undefined;
  private historyRefreshTimer$: Subscription | undefined;
  private loadingJobLogs = signal(false);
  private loadingHistory = signal(false);
  private loadingInstance = signal(false);

  loadJobLogs: WritableSignal<boolean> = signal(false);
  loadHistory: WritableSignal<boolean> = signal(true);

  constructor() {
    this.instance = signal(this.dialogData.instance);
    this.instanceFilters.model_id = this.instance().model_instance.model_id;
    this.instanceFilters.work_request_id = `${this.instance().model_instance.work_request_id}`;

    this.jobLogsFilters.model_id = this.instance().model_instance.model_id;
    this.jobLogsFilters.work_request_id = `${this.instance().model_instance.work_request_id}`;

    this.startRefreshTimers();
  }

  ngOnDestroy() {
    this.instanceRefreshTimer$?.unsubscribe();
    this.instanceRefreshTimer$ = undefined;
    this.jobLogsRefreshTimer$?.unsubscribe();
    this.jobLogsRefreshTimer$ = undefined;
    this.historyRefreshTimer$?.unsubscribe();
    this.historyRefreshTimer$ = undefined;
  }

  startRefreshTimers() {
    if (this.instanceRefreshTimer$ == null) {
      this.instanceRefreshTimer$ = timer(0, 3000).subscribe(_ => {
        if (this.loadingInstance()) {
          return;
        }

        this.loadingInstance.set(true);
        this.instancesService.loadInstance(this.instanceFilters).subscribe({
          next: result => {
            if (result != null) {
              this.instance.set(result);
            }

          },
          error: (err: Error) => {
            this.loadingInstance.set(false);
          }
        })
      });
    }

    if (this.jobLogsRefreshTimer$ == null) {
      this.jobLogsRefreshTimer$ = timer(0, 3000).subscribe(_ => {
        if (!this.loadJobLogs() || this.loadingJobLogs()) {
          return;
        }

        this.loadingJobLogs.set(true);
        this.instancesService.loadInstanceJobLogs(this.jobLogsFilters).subscribe({
          next: result => {
            if (result != null) {
              this.jobLogs.set(result);
            }

            this.loadingJobLogs.set(false);
          },
          error: (err: Error) => {
            this.loadingJobLogs.set(false);
          }
        })
      });
    }

    if (this.historyRefreshTimer$ == null) {
      this.historyRefreshTimer$ = timer(0, 3000).subscribe(_ => {
        if (!this.loadHistory() || this.loadingHistory()) {
          return;
        }

        this.loadingHistory.set(true);
        this.instancesService.loadInstanceHistory(this.instanceFilters).subscribe({
          next: result => {
            if (result != null) {
              this.history.set(result);
            }

            this.loadingHistory.set(false);
          },
          error: (err: Error) => {
            this.loadingHistory.set(false);
          }
        })
      });
    }
  }

  get jobLogsTail(): string {
    return this.jobLogsFilters.tail ? `${this.jobLogsFilters.tail}` : 'ALL';
  }

  set jobLogsTail(value: string) {
    if (value == null || value == 'ALL') {
      delete this.jobLogsFilters['tail'];
    } else {
      this.jobLogsFilters.tail = Number.parseInt(value);
    }
  }

  get jobLogsHead(): string {
    return this.jobLogsFilters.head ? `${this.jobLogsFilters.head}` : 'ALL';
  }

  set jobLogsHead(value: string) {
    if (value == null || value == 'ALL') {
      delete this.jobLogsFilters['head'];
    } else {
      this.jobLogsFilters.head = Number.parseInt(value);
    }
  }


  close() {
    this.dialogRef.close();
  }

  trackBy: TrackByFunction<InstanceLogEntry> = (index: number, item: InstanceLogEntry) => {
    return `${item.log_event}_${item.log_timestamp}`;
  };

  instanceDetailsSummary = (details: K8sPod | undefined) => {
    if (details == null) {
      return '';
    }

    const template = '<span><span>LABEL: </span><span>VALUE</span></span>';

    let summary = '';
    summary += template.replace('LABEL', 'name').replace('VALUE', details.name);
    summary += template.replace('LABEL', 'phase').replace('VALUE', details.state.phase);
    summary += template.replace('LABEL', 'started').replace('VALUE', `${details.state.started}`);
    summary += template.replace('LABEL', 'ready').replace('VALUE', `${details.state.ready}`);

    return summary;
  };


}
