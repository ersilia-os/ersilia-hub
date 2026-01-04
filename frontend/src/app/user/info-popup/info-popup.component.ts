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
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { ErsiliaLoaderComponent } from '../../ersilia-loader/ersilia-loader.component';
import { NotificationsService, Notification } from '../../notifications/notifications.service';
import { AbstractControl, Form, FormControl, FormGroupDirective, FormsModule, NgForm, ReactiveFormsModule, Validators } from "@angular/forms";
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { UsersService } from '../../../services/users.service';
import { User } from '../../../objects/user';
import { AuthService } from '../../../services/auth.service';
import { UpdateUserPasswordComponent } from '../update-user-password/update-user-password.component';
import { UpdateUserPermissionsComponent } from '../update-user-permissions/update-user-permissions.component';
import { DeleteUserComponent } from '../delete-user/delete-user.component';

@Component({
  standalone: true,
  imports: [
    MatButtonModule, CommonModule, MatIconModule, MatProgressBarModule,
    MatDialogActions, MatDialogClose, MatDialogTitle, MatDialogContent,
    MatFormFieldModule, MatSelectModule, FormsModule, MatInputModule, ErsiliaLoaderComponent,
    ReactiveFormsModule, MatTooltipModule, MatCheckboxModule
  ],
  templateUrl: './info-popup.component.html',
  styleUrl: './info-popup.component.scss'
})
export class UserInfoPopupComponent implements OnInit {
  readonly dialogRef = inject(MatDialogRef<UserInfoPopupComponent>);
  readonly dialogData = inject(MAT_DIALOG_DATA);
  readonly dialog = inject(MatDialog);

  busy: WritableSignal<boolean> = signal(true);

  user: User | undefined = undefined;
  isOwnUser: boolean = true;
  isUserAdmin: boolean = false;

  private usersService = inject(UsersService);
  private authService = inject(AuthService);
  private notificationsService = inject(NotificationsService);

  submitting: WritableSignal<boolean> = signal(false);

  constructor() {
  }

  ngOnInit() {
    this.user = this.dialogData;

    if (this.user == null) {
      this.busy.set(false);
      return;
    }

    this.isOwnUser = this.authService.computeUserSignal(user => user?.id === this.user?.id)();
    this.isUserAdmin = this.authService.computePermissionsSignal(permissions => permissions.includes("ADMIN"))();

    this.busy.set(false);
  }

  canEdit() {
    return this.isOwnUser || this.isUserAdmin;
  }

  canSubmit() {
    return this.user != null
      && !this.busy()
      && !this.submitting()
      && this.canEdit();
  }

  clearContributions() {
    if (!this.canSubmit()) {
      return;
    }

    this.submitting.set(true);

    this.usersService.clearUserContributions(this.user?.id!).subscribe({
      next: result => {
        this.submitting.set(false);
        this.notificationsService.pushNotification(Notification("SUCCESS", "Successfully cleared contributions"));
      },
      error: (err: Error) => {
        this.notificationsService.pushNotification(Notification("ERROR", "Failed to clear user contributions"));
        this.submitting.set(false);
      }
    });
  }

  clearData() {
    if (!this.canSubmit()) {
      return;
    }

    this.submitting.set(true);

    this.usersService.clearUserData(this.user?.id!).subscribe({
      next: result => {
        this.submitting.set(false);
        this.notificationsService.pushNotification(Notification("SUCCESS", "Successfully cleared data"));
      },
      error: (err: Error) => {
        this.notificationsService.pushNotification(Notification("ERROR", "Failed to clear user data"));
        this.submitting.set(false);
      }
    });
  }

  openPasswordUpdateDialog() {
    if (!this.canEdit()) {
      return;
    }

    this.dialog.open(UpdateUserPasswordComponent, {
      enterAnimationDuration: '300ms',
      exitAnimationDuration: '300ms',
      panelClass: 'dialog-panel',
      data: this.user,
    });
  }

  openPermissionsUpdateDialog() {
    if (!this.isUserAdmin) {
      return;
    }

    this.dialog.open(UpdateUserPermissionsComponent, {
      enterAnimationDuration: '300ms',
      exitAnimationDuration: '300ms',
      panelClass: 'dialog-panel',
      data: this.user,
    });
  }

  openUserDeleteDialog() {
    if (!this.isUserAdmin && !this.isOwnUser) {
      return;
    }

    this.dialog.open(DeleteUserComponent, {
      enterAnimationDuration: '300ms',
      exitAnimationDuration: '300ms',
      panelClass: 'dialog-panel',
      data: this.user,
    }).afterClosed().subscribe(_ => {
      this.close();
    })
  }

  logout() {
    if (!this.isOwnUser) {
      return;
    }

    this.authService.logout().subscribe(_ => this.close());
  }

  close() {
    this.busy.set(false);
    this.dialogRef.close();
  }
}

