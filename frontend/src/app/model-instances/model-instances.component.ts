import { Component, inject, OnDestroy, Signal, TrackByFunction } from '@angular/core';
import { Subscription, timer } from 'rxjs';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog } from '@angular/material/dialog';
import { ErsiliaLoaderComponent } from '../ersilia-loader/ersilia-loader.component';
import { InstancesService } from '../../services/instances.service';
import { ACTIVE_STATES, ExtendedModelInstance, ModelInstance, ModelInstanceFilters, ModelInstanceState, TERMINATED_STATES } from '../../objects/instance';
import { ModelInstanceResourceComponent } from '../model-instance-resource/model-instance-resource.component';
import { MatFormFieldModule } from '@angular/material/form-field';
import { FormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { ModelsService } from '../../services/models.service';
import { Model } from '../../objects/model';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ModelInstanceMonitorComponent } from './model-instance-monitor/model-instance-monitor.component';

@Component({
  selector: 'app-model-instances',
  standalone: true,
  imports: [
    MatButtonModule,
    FormsModule,
    MatFormFieldModule,
    CommonModule,
    MatIconModule, MatCheckboxModule, MatSelectModule,
    MatProgressBarModule,
    ErsiliaLoaderComponent, ModelInstanceResourceComponent],
  templateUrl: './model-instances.component.html',
  styleUrl: './model-instances.component.scss'
})
export class ModelInstancesComponent implements OnDestroy {

  private instancesService = inject(InstancesService);
  private modelsService = inject(ModelsService);
  private refreshTimer$: Subscription | undefined;
  private instanceFilters: ModelInstanceFilters = {
    states: [...ACTIVE_STATES],
    load_resource_profiles: true,
    load_recommendations: true
  };

  readonly dialog = inject(MatDialog);

  instances: Signal<ExtendedModelInstance[]>;
  loading: Signal<boolean>;
  models: Signal<Model[]>
  modelsLoading: Signal<boolean>;

  constructor() {
    this.loading = this.instancesService.computeInstancesLoadingSignal<boolean>(
      _loading => this.instances == null || (this.instances().length == 0 && _loading)
    );

    this.instances = this.instancesService.getInstancesSignal();
    this.models = this.modelsService.computeModelsSignal(models => models.filter(m => m.enabled));
    this.modelsLoading = this.modelsService.computeModelsLoadingSignal(_loading => {
      return this.models == null || _loading
    });

    if (this.shouldEnableAutoRefresh()) {
      this.startRefreshTimer();
    }
  }

  get filtersLoadActive(): boolean {
    return this.instanceFilters.states!.includes(ModelInstanceState.ACTIVE);
  }

  set filtersLoadActive(value: boolean) {
    if (value) {
      ACTIVE_STATES.forEach(state => {
        if (!this.instanceFilters.states!.includes(state)) {
          this.instanceFilters.states?.push(state);
        }
      })
    } else {
      this.instanceFilters.states = this.instanceFilters.states?.filter(state => !ACTIVE_STATES.includes(state))
    }
  }

  get filtersLoadTerminated(): boolean {
    return this.instanceFilters.states!.includes(ModelInstanceState.TERMINATED);
  }

  set filtersLoadTerminated(value: boolean) {
    if (value) {
      TERMINATED_STATES.forEach(state => {
        if (!this.instanceFilters.states!.includes(state)) {
          this.instanceFilters.states?.push(state);
        }
      })
    } else {
      this.instanceFilters.states = this.instanceFilters.states?.filter(state => !TERMINATED_STATES.includes(state))
    }
  }

  get filtersLoadMetrics(): boolean {
    return (this.instanceFilters.load_recommendations ?? false) && (this.instanceFilters.load_resource_profiles ?? false);
  }

  set filtersLoadMetrics(value: boolean) {
    this.instanceFilters.load_recommendations = value;
    this.instanceFilters.load_resource_profiles = value;
  }

  get filtersModel() {
    return this.instanceFilters.model_id;
  }

  set selectedModel(value: string | undefined) {
    this.instanceFilters.model_id = value;
  }

  ngOnDestroy() {
    this.refreshTimer$?.unsubscribe();
    this.refreshTimer$ = undefined;
  }

  startRefreshTimer() {
    if (this.refreshTimer$ != null) {
      return;
    }

    this.refreshTimer$ = timer(0, 5000).subscribe(_ => {
      if (!this.autoRefreshEnabled()) {
        this.refreshTimer$?.unsubscribe();
        this.refreshTimer$ = undefined;
        return;
      }

      this.instancesService.loadInstances(this.instanceFilters);
    });
  }

  hasRequests(): boolean {
    return this.instances != null && this.instances().length > 0;
  }

  shouldEnableAutoRefresh(): boolean {
    // fluffy logic based on filters
    return !this.instanceFilters.states!.includes(ModelInstanceState.TERMINATED);
  }

  autoRefreshEnabled(): boolean {
    return this.refreshTimer$ != null;
  }

  load() {
    if (this.loading() || this.autoRefreshEnabled()) {
      return;
    }

    if (this.shouldEnableAutoRefresh()) {
      this.startRefreshTimer();
      return;
    }

    this.instancesService.loadInstances(this.instanceFilters);
  }

  trackBy: TrackByFunction<ExtendedModelInstance> = (index: number, item: ExtendedModelInstance) => {
    return `${item.model_instance.model_id}_${item.model_instance.work_request_id}_${item.model_instance.last_updated}`;
  };

  viewDetailedInstance(instance: ExtendedModelInstance) {
    if (this.dialog != null && this.dialog.openDialogs.length > 0) {
      return;
    }

    this.dialog.open(ModelInstanceMonitorComponent, {
      enterAnimationDuration: '300ms',
      exitAnimationDuration: '300ms',
      panelClass: 'dialog-panel-large',
      data: {
        instance: instance
      }
    });
  }
}
