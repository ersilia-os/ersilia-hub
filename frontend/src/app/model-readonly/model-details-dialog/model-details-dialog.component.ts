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

  constructor() {
  }

  ngOnInit() {
    this.model = this.dialogData;
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
      panelClass: 'dialog-panel',
      data: model,
    });
  }
}

