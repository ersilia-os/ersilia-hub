import { Component, inject, OnInit, signal, WritableSignal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import {
  MAT_DIALOG_DATA,
  MatDialog,
  MatDialogActions,
  MatDialogClose,
  MatDialogContent,
  MatDialogRef,
  MatDialogTitle,
} from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { ErsiliaLoaderComponent } from '../../ersilia-loader/ersilia-loader.component';
import { FormsModule } from "@angular/forms";
import { MatTooltipModule } from '@angular/material/tooltip';
import { Model } from '../../../objects/model';
import { RequestsCreateComponent } from '../../request-create/request-create.component';

/**
 * Resolve a metadata value into a followable URL, or null when it is not one.
 *
 * Publication fields hold either a full URL or a bare DOI; source code fields
 * occasionally omit the scheme.
 */
function toExternalUrl(value?: string): string | null {
  const trimmed = value?.trim();

  if (!trimmed) {
    return null;
  }

  if (/^https?:\/\/\S+$/i.test(trimmed)) {
    return trimmed;
  }

  if (/^(doi:)?10\.\d{4,9}\/\S+$/i.test(trimmed)) {
    return `https://doi.org/${trimmed.replace(/^doi:/i, '')}`;
  }

  if (/^www\.\S+$/i.test(trimmed)) {
    return `https://${trimmed}`;
  }

  return null;
}

@Component({
  standalone: true,
  imports: [
    MatButtonModule, CommonModule, MatIconModule, MatProgressBarModule,
    MatDialogActions, MatDialogClose, MatDialogTitle, MatDialogContent,
    MatFormFieldModule, FormsModule, ErsiliaLoaderComponent,
    MatTooltipModule
  ],
  templateUrl: './model-details-dialog.component.html',
  styleUrl: './model-details-dialog.component.scss'
})
export class ModelDetailsDialogComponent implements OnInit {
  readonly dialogRef = inject(MatDialogRef<ModelDetailsDialogComponent>);
  readonly dialogData = inject(MAT_DIALOG_DATA);
  readonly dialog = inject(MatDialog);

  busy: WritableSignal<boolean> = signal(true);

  model: Model | undefined = undefined;
  publicationUrl: string | null = null;
  sourceCodeUrl: string | null = null;

  constructor() {
  }

  ngOnInit() {
    this.model = this.dialogData;

    const details = this.model?.details?.identification_details;
    this.publicationUrl = toExternalUrl(details?.publication);
    this.sourceCodeUrl = toExternalUrl(details?.source_code);

    this.busy.set(false);
  }

  close() {
    this.busy.set(false);
    this.dialogRef.close();
  }

  openCreateRequestDialog(model: Model | undefined) {
    if (model == null) {
      return;
    }

    this.dialog.open(RequestsCreateComponent, {
      enterAnimationDuration: '300ms',
      exitAnimationDuration: '300ms',
      panelClass: 'dialog-panel-large',
      data: model,
    });
  }
}

