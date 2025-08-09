import { Component, inject, OnDestroy, Signal, TrackByFunction } from '@angular/core';
import { Subscription, timer } from 'rxjs';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog } from '@angular/material/dialog';
import { ErsiliaLoaderComponent } from '../ersilia-loader/ersilia-loader.component';
import { InstancesService } from '../../services/instances.service';
import { ModelInstance, ModelInstanceFilters } from '../../objects/instance';
import { ModelInstanceResourceComponent } from '../model-instance-resource/model-instance-resource.component';
import { MatFormFieldModule } from '@angular/material/form-field';
import { FormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';

@Component({
  selector: 'app-model-instances',
  standalone: true,
  imports: [MatButtonModule, FormsModule, MatFormFieldModule, CommonModule, MatIconModule, MatCheckboxModule,
    ErsiliaLoaderComponent, ModelInstanceResourceComponent],
  templateUrl: './model-instances.component.html',
  styleUrl: './model-instances.component.scss'
})
export class ModelInstancesComponent implements OnDestroy {

  private instancesService = inject(InstancesService);
  private refreshTimer$: Subscription | undefined;
  private instanceFilters: ModelInstanceFilters = {
    active: true,
    persisted: false,
    load_resource_profiles: true,
    load_recommendations: true
  };

  readonly dialog = inject(MatDialog);

  instances: Signal<ModelInstance[]>;
  loading: Signal<boolean>;

  constructor() {

    this.loading = this.instancesService.computeInstancesLoadingSignal<boolean>(
      _loading => this.instances == null || (this.instances().length == 0 && _loading)
    );

    this.instances = this.instancesService.getInstancesSignal();

    if (this.autoRefreshEnabled()) {
      this.startRefreshTimer();
    }
  }

  get filtersLoadActive(): boolean {
    return this.instanceFilters.active ?? false;
  }

  set filtersLoadActive(value: boolean) {
    this.instanceFilters.active = value;
  }

  get filtersLoadPersisted(): boolean {
    return this.instanceFilters.persisted ?? false;
  }

  set filtersLoadPersisted(value: boolean) {
    this.instanceFilters.persisted = value;
  }

  get filtersLoadMetrics(): boolean {
    return (this.instanceFilters.load_recommendations ?? false) && (this.instanceFilters.load_resource_profiles ?? false);
  }

  set filtersLoadMetrics(value: boolean) {
    this.instanceFilters.load_recommendations = value;
    this.instanceFilters.load_resource_profiles = value;
  }

  ngOnDestroy() {
    this.refreshTimer$?.unsubscribe();
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

  autoRefreshEnabled(): boolean {
    // fluffy logic based on filters
    return !this.instanceFilters.persisted && this.refreshTimer$ != null;
  }

  load() {
    if (this.loading() || this.autoRefreshEnabled()) {
      return;
    }

    if (!this.instanceFilters.persisted) {
      this.startRefreshTimer();
      return;
    }

    this.instancesService.loadInstances(this.instanceFilters);
  }

  trackBy: TrackByFunction<ModelInstance> = (index: number, item: ModelInstance) => {
    return `${item.k8s_pod.name}_${item.resource_profile == null}_${item.resource_recommendations == null ? '' : item.resource_recommendations.last_updated}`;
  };

  /**
   * TODO: open dialog for model recommendations ?? -> load for specific model
   */

  /**
   * TODO: open model for model management (enable / disable, change request / limits, etc.)
   */

  // openCreateRequestDialog(): void {
  //   if (this.dialog != null && this.dialog.openDialogs.length > 0) {
  //     return;
  //   }

  //   this.dialog.open(RequestsCreateComponent, {
  //     enterAnimationDuration: '300ms',
  //     exitAnimationDuration: '300ms',
  //     panelClass: 'dialog-panel'
  //   });
  // }

  // viewRequest(request: RequestDisplay) {
  //   this.dialog.open(RequestViewComponent, {
  //     enterAnimationDuration: '300ms',
  //     exitAnimationDuration: '300ms',
  //     panelClass: 'dialog-panel',
  //     data: request,
  //   });
  // }

  /**
   * TODO: instance actions (remove / logs ??)
   */
}
