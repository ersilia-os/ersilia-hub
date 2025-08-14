import { Component, inject, OnInit, signal, Signal, TrackByFunction, WritableSignal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog } from '@angular/material/dialog';
import { ErsiliaLoaderComponent } from '../ersilia-loader/ersilia-loader.component';
import { MatFormFieldModule } from '@angular/material/form-field';
import { FormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { ModelsService } from '../../services/models.service';
import { Model } from '../../objects/model';

@Component({
  selector: 'app-model-management',
  standalone: true,
  imports: [MatButtonModule, FormsModule, MatFormFieldModule, CommonModule, MatIconModule, MatCheckboxModule,
    ErsiliaLoaderComponent],
  templateUrl: './model-management.component.html',
  styleUrl: './model-management.component.scss'
})
export class ModelManagementComponent implements OnInit {

  private modelsService = inject(ModelsService);
  private pageFilters: WritableSignal<PageFilters> = signal({});

  readonly dialog = inject(MatDialog);

  models: Signal<Model[]>;
  loading: Signal<boolean>;

  displayedColumns: string[] = ['enabled', 'id', 'description', 'resources', 'max_instances', 'exec_mode', 'actions'];
  columnHeaders: { [column: string]: string } = {
    enabled: 'Enabled',
    id: 'Model Id',
    description: 'Description',
    resources: 'Resources',
    max_instances: 'Max Instances',
    exec_mode: 'Execution Mode',
    actions: ''
  };

  constructor() {
    this.loading = this.modelsService.getModelsLoadingSignal();
    this.models = this.modelsService.computeModelsSignal(models => {
      const pageFilters = this.pageFilters();

      return models.filter(model => {
        return (pageFilters.activeOnly && !model.enabled)
          && (pageFilters.searchString && !model.id.startsWith(pageFilters.searchString));
      });
    });
  }

  get filtersActiveOnly(): boolean {
    return this.pageFilters().activeOnly ?? false;
  }

  set filtersActiveOnly(value: boolean) {
    this.pageFilters.set({
      ...this.pageFilters(),
      activeOnly: value
    });
  }

  get filtersSearchString(): string | undefined {
    return this.pageFilters().searchString;
  }

  set filtersSearchString(value: string | undefined) {
    this.pageFilters.set({
      ...this.pageFilters(),
      searchString: value
    });
  }

  ngOnInit() {
    this.load();
  }

  load() {
    if (this.loading()) {
      return;
    }

    this.modelsService.loadModels();
  }

  trackBy: TrackByFunction<Model> = (index: number, item: Model) => {
    return `${item.id}_${item.last_updated}`;
  };

  createModel() {
    // TODO: open dialog
  }

  editModel() {
    // TODO: open dialog
  }
}

interface PageFilters {
  searchString?: string;
  activeOnly?: boolean;
}