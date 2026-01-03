import { Component, inject, OnInit, signal, WritableSignal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import {
  MAT_DIALOG_DATA,
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
import { Permission, PermissionsList } from '../../../objects/auth';

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

  busy: WritableSignal<boolean> = signal(true);

  user: User | undefined = undefined;
  isOwnUser: boolean = true;
  isUserAdmin: boolean = false;

  permissions: PermissionState[];
  originalPermissionsList: Permission[] = [];

  private usersService = inject(UsersService);
  private authService = inject(AuthService);
  private notificationsService = inject(NotificationsService);

  submitting: WritableSignal<boolean> = signal(false);

  constructor() {
    this.permissions = PermissionsList.map(p => {
      return {
        permission: p,
        state: false
      };
    });
  }

  ngOnInit() {
    this.user = this.dialogData;

    if (this.user == null) {
      this.busy.set(false);
      return;
    }

    this.isOwnUser = this.authService.computeUserSignal(user => user?.id === this.user?.id)();
    this.isUserAdmin = this.authService.computePermissionsSignal(permissions => permissions.includes("ADMIN"))();

    if (this.isUserAdmin) {
      this.permissions = this.authService.computePermissionsSignal(permissions => {
        return PermissionsList.map(pl => {
          return {
            permission: pl,
            state: permissions.includes(pl)
          } as PermissionState;
        })
      })();
      this.originalPermissionsList = this.permissions.filter(p => p.state).map(p => p.permission);
    }

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

  canSubmitPasswordReset(): boolean {
    return this.canSubmit()
    //  &&
    // TODO: validity / inputs check
  }

  updatePassword() {
    if (!this.canSubmitPasswordReset()) {
      return;
    }
    // TODO: if OWN user, curr + new password
    // TODO: else force flag + new password
  }

  deleteUser() {
    if (!this.canSubmit()) {
      return;
    }
    // TODO: additional dialog (does 2 dialogs work?)
    // TODO: close THIS dialog on success
  }

  canSubmitPermissionsUpdate(): boolean {
    return this.canSubmit()
      && hasPermissionsChange(this.permissions, this.originalPermissionsList);
  }

  updatePermissions() {
    if (!this.canSubmitPermissionsUpdate()) {
      return;
    }

    try {
      this.usersService.updateUserPermissions(this.user?.id!, permissionsToList(this.permissions))
        .subscribe(_ => {
          this.originalPermissionsList = permissionsToList(this.permissions);
          this.submitting.set(false);
          this.notificationsService.pushNotification(Notification("SUCCESS", "Sucessfully updated permissions"));
        })
    } catch (e) {
      this.notificationsService.pushNotification(Notification("ERROR", "Failed to update permissions"));
      this.submitting.set(false);
    }
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

interface PermissionState {
  permission: Permission;
  state: boolean;
}

function permissionsToList(permissions: PermissionState[]): Permission[] {
  return permissions.filter(p => p.state).map(p => p.permission);
}

function hasPermissionsChange(permissions: PermissionState[], originalPermissions: Permission[]): boolean {
  for (const permission of permissions) {
    // newly set true
    if (permission.state && !originalPermissions.includes(permission.permission)) {
      return true;
    }

    // newly set false
    if (!permission.state && originalPermissions.includes(permission.permission)) {
      return true;
    }
  }

  return false;
}
