import { Component, inject, OnDestroy, Signal } from '@angular/core';
import { Subscription, timer } from 'rxjs';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog } from '@angular/material/dialog';
import { ErsiliaLoaderComponent } from '../ersilia-loader/ersilia-loader.component';
import { InstancesService } from '../../services/instances.service';
import { ModelInstance, ModelInstanceFilters } from '../../objects/instance';
import { ModelInstanceResourceComponent } from '../model-instance-resource/model-instance-resource.component';

@Component({
  selector: 'app-model-instances',
  standalone: true,
  imports: [MatButtonModule, CommonModule, MatIconModule, ErsiliaLoaderComponent, ModelInstanceResourceComponent],
  templateUrl: './model-instances.component.html',
  styleUrl: './model-instances.component.scss'
})
export class ModelInstancesComponent implements OnDestroy {

  private instancesService = inject(InstancesService);
  private refreshTimer$: Subscription | undefined;
  private instanceFilters: ModelInstanceFilters = {
    active: true,
    persisted: true,
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
      this.refreshTimer$ = timer(0, 5000).subscribe(_ => {
        this.instancesService.loadInstances(this.instanceFilters);
      });
    }
  }

  /**
   * TODO: if we change the filters to include non-active instances, STOP auto-refresh
   */

  ngOnDestroy() {
    this.refreshTimer$?.unsubscribe();
  }

  hasRequests(): boolean {
    return this.instances != null && this.instances().length > 0;
  }

  autoRefreshEnabled(): boolean {
    // fluffy logic based on filters
    return !this.instanceFilters.persisted;
  }

  load() {
    if (this.loading() || this.autoRefreshEnabled()) {
      return;
    }

    this.instancesService.loadInstances(this.instanceFilters);
  }

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
