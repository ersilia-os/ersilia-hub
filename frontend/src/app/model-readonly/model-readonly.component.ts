import { Component, computed, inject, OnInit, signal, Signal, TrackByFunction, WritableSignal } from '@angular/core';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ErsiliaLoaderComponent } from '../ersilia-loader/ersilia-loader.component';
import { ModelsService } from '../../services/models.service';
import { filterModels, Model, ModelFilter } from '../../objects/model';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { FormsModule } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { ModelDetailsDialogComponent } from './model-details-dialog/model-details-dialog.component';
import { RequestsCreateComponent } from '../request-create/request-create.component';
import { MatTooltipModule } from '@angular/material/tooltip';

@Component({
  selector: 'app-model-readonly',
  standalone: true,
  imports: [
    MatButtonModule, MatTableModule, CommonModule, MatIconModule, MatProgressBarModule,
    ErsiliaLoaderComponent, MatFormFieldModule, MatInputModule, FormsModule, MatTooltipModule
  ],
  templateUrl: './model-readonly.component.html',
  styleUrl: './model-readonly.component.scss'
})
export class ModelReadonlyComponent implements OnInit {

  private modelsService = inject(ModelsService);
  readonly dialog = inject(MatDialog);

  models: Signal<Model[]>;
  filteredModels: Signal<Model[]>;
  filters: WritableSignal<ModelFilter> = signal({ id: undefined, description: undefined });
  loading: Signal<boolean>;

  displayedColumns: string[] = ['id', 'description'];
  columnHeaders: { [column: string]: string } = {
    id: 'id',
    description: 'Description',
  };

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

  constructor() {
    this.loading = this.modelsService.computeModelsLoadingSignal<boolean>(
      _loading => this.models == null || (this.models().length == 0 && _loading)
    );

    this.models = this.modelsService.computeModelsSignal(models => models.filter(m => m.enabled));
    this.filteredModels = computed(() => filterModels(this.models(), this.filters()));
  }

  ngOnInit() {
    this.modelsService.loadModels();
  }

  hasModels(): boolean {
    return this.models != null && this.models().length > 0;
  }

  tableTrackBy: TrackByFunction<Model> = (index: number, item: Model) => {
    return `${item.id}_${item.last_updated}`;
  };

  openDetailsDialog(model: Model) {
    this.dialog.open(ModelDetailsDialogComponent, {
      enterAnimationDuration: '300ms',
      exitAnimationDuration: '300ms',
      panelClass: 'dialog-panel-large',
      data: model,
    });
  }

  openRequestForm(model: Model) {
    this.dialog.open(RequestsCreateComponent, {
      enterAnimationDuration: '300ms',
      exitAnimationDuration: '300ms',
      panelClass: 'dialog-panel',
      data: model,
    });
  }

}
