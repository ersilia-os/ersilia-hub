import { Component, computed, inject, OnInit, signal, Signal, TrackByFunction, WritableSignal } from '@angular/core';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ErsiliaLoaderComponent } from '../ersilia-loader/ersilia-loader.component';
import { ModelsService } from '../../services/models.service';
import { filterModels, Model, ModelFilter } from '../../objects/model';
import { FormsModule } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { ModelDetailsDialogComponent } from './model-details-dialog/model-details-dialog.component';
import { RequestsCreateComponent } from '../request-create/request-create.component';
import { MatTooltipModule } from '@angular/material/tooltip';

/** Approximate character count that fills the 3-line description clamp on a card. */
const DESCRIPTION_CLAMP_CHARS = 130;

@Component({
  selector: 'app-model-readonly',
  standalone: true,
  imports: [
    MatButtonModule, MatTableModule, CommonModule, MatIconModule, MatProgressBarModule,
    ErsiliaLoaderComponent, FormsModule, MatTooltipModule
  ],
  templateUrl: './model-readonly.component.html',
  styleUrl: './model-readonly.component.scss'
})
export class ModelReadonlyComponent implements OnInit {

  private modelsService = inject(ModelsService);
  readonly dialog = inject(MatDialog);

  models: Signal<Model[]>;
  filteredModels: Signal<Model[]>;
  countLabel: Signal<string>;
  filters: WritableSignal<ModelFilter> = signal({ freeText: undefined, id: undefined, description: undefined });
  loading: Signal<boolean>;
  expandedModelIds: WritableSignal<Set<string>> = signal(new Set<string>());

  displayedColumns: string[] = ['id', 'description'];
  columnHeaders: { [column: string]: string } = {
    id: 'id',
    description: 'Description',
  };

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

  constructor() {
    this.loading = this.modelsService.computeModelsLoadingSignal<boolean>(
      _loading => this.models == null || (this.models().length == 0 && _loading)
    );

    this.models = this.modelsService.computeModelsSignal(models => models.filter(m => m.enabled));
    this.filteredModels = computed(() => filterModels(this.models(), this.filters()));

    this.countLabel = computed(() => {
      const total = this.models().length;
      const shown = this.filteredModels().length;

      return shown === total ? `${total} available` : `${shown} of ${total} shown`;
    });
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

  /** Card title: the model title, falling back to its slug. */
  modelTitle(model: Model): string {
    const details = model.details.identification_details;
    return details?.title?.trim() || details?.slug?.trim() || '';
  }

  /** Shown beside the id, unless the card is already using it as its title. */
  modelSlug(model: Model): string {
    const slug = model.details.identification_details?.slug?.trim() || '';
    return slug === this.modelTitle(model) ? '' : slug;
  }

  modelDescription(model: Model): string {
    const details = model.details.identification_details;
    return details?.description?.trim() || model.details.description?.trim() || '';
  }

  isExpanded(model: Model): boolean {
    return this.expandedModelIds().has(model.id);
  }

  /** Descriptions shorter than ~3 rendered lines never need a toggle. */
  canExpand(model: Model): boolean {
    return this.modelDescription(model).length > DESCRIPTION_CLAMP_CHARS;
  }

  toggleExpanded(model: Model, event: MouseEvent) {
    event.stopPropagation();

    const expanded = new Set(this.expandedModelIds());

    if (expanded.has(model.id)) {
      expanded.delete(model.id);
    } else {
      expanded.add(model.id);
    }

    this.expandedModelIds.set(expanded);
  }

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
      panelClass: 'dialog-panel-large',
      data: model,
    });
  }

}
