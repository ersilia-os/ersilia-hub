import { Component, inject, OnInit, signal, TrackByFunction, WritableSignal } from '@angular/core';
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
import { Permission, PermissionsList } from '../../../objects/auth';
import { ErrorStateMatcher } from '@angular/material/core';
import { UpdateUserPasswordComponent } from '../update-user-password/update-user-password.component';

@Component({
  standalone: true,
  imports: [
    MatButtonModule, CommonModule, MatIconModule, MatProgressBarModule,
    MatDialogActions, MatDialogClose, MatDialogTitle, MatDialogContent,
    MatFormFieldModule, MatSelectModule, FormsModule, MatInputModule, ErsiliaLoaderComponent,
    ReactiveFormsModule, MatTooltipModule, MatCheckboxModule
  ],
  templateUrl: './update-user-permissions.component.html',
  styleUrl: './update-user-permissions.component.scss'
})
export class UpdateUserPermissionsComponent implements OnInit {
  readonly dialogRef = inject(MatDialogRef<UpdateUserPermissionsComponent>);
  readonly dialogData = inject(MAT_DIALOG_DATA);

  busy: WritableSignal<boolean> = signal(true);

  user: User | undefined = undefined;
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

  toggleState(permission: PermissionState, newState: boolean) {
    if (this.submitting()) {
      return;
    }

    permission.state = newState;
  }

  canEdit() {
    return this.isUserAdmin;
  }

  canSubmit() {
    return this.user != null
      && !this.busy()
      && !this.submitting()
      && this.canEdit();
  }

  canSubmitPermissionsUpdate(): boolean {
    return this.canSubmit()
      && hasPermissionsChange(this.permissions, this.originalPermissionsList);
  }

  updatePermissions() {
    if (!this.canSubmitPermissionsUpdate()) {
      return;
    }

    this.submitting.set(true);

    this.usersService.updateUserPermissions(this.user?.id!, permissionsToList(this.permissions))
      .subscribe({
        next: result => {
          this.originalPermissionsList = permissionsToList(this.permissions);
          this.submitting.set(false);
          this.notificationsService.pushNotification(Notification("SUCCESS", "Successfully updated user permissions"));
          this.close();
        },
        error: (err: Error) => {
          this.notificationsService.pushNotification(Notification("ERROR", "Failed to update user permissions"));
          this.submitting.set(false);
        }
      });
  }

  close() {
    this.busy.set(false);
    this.dialogRef.close();
  }

  trackBy: TrackByFunction<PermissionState> = (index: number, item: PermissionState) => {
    return `${item.permission}_${item.state}`;
  };
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

