import { Component, computed, inject, OnInit, signal, Signal, TrackByFunction, WritableSignal } from '@angular/core';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ErsiliaLoaderComponent } from '../ersilia-loader/ersilia-loader.component';
import { ModelsService } from '../../services/models.service';
import { Model } from '../../objects/model';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-model-readonly',
  standalone: true,
  imports: [
    MatButtonModule, MatTableModule, CommonModule, MatIconModule, MatProgressBarModule,
    ErsiliaLoaderComponent, MatFormFieldModule, MatInputModule, FormsModule
  ],
  templateUrl: './model-readonly.component.html',
  styleUrl: './model-readonly.component.scss'
})
export class ModelReadonlyComponent implements OnInit {

  private modelsService = inject(ModelsService);

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

    this.models = this.modelsService.getModelsSignal();
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
}

interface ModelFilter {
  id: string | undefined;
  description: string | undefined;
}

function filterModels(models: Model[], filters: ModelFilter): Model[] {
  return models.filter(model =>
    checkId(model, filters.id)
    && checkDescription(model, filters.description)
  )
}

function checkId(model: Model, filter: string | undefined): boolean {
  return filter == null || (model.id != null && model.id.includes(filter));
}

function checkDescription(model: Model, filter: string | undefined): boolean {
  return filter == null || (model.details.description != null && model.details.description.includes(filter));
}
