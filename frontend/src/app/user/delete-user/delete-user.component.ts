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
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { UsersService } from '../../../services/users.service';
import { User } from '../../../objects/user';
import { AuthService } from '../../../services/auth.service';
import { FormsModule } from '@angular/forms';

@Component({
  standalone: true,
  imports: [
    MatButtonModule, CommonModule, MatIconModule, MatProgressBarModule,
    MatDialogActions, MatDialogClose, MatDialogTitle, MatDialogContent,
    MatFormFieldModule, MatSelectModule, FormsModule, MatInputModule, ErsiliaLoaderComponent,
    MatTooltipModule, MatCheckboxModule
  ],
  templateUrl: './delete-user.component.html',
  styleUrl: './delete-user.component.scss'
})
export class DeleteUserComponent implements OnInit {
  readonly dialogRef = inject(MatDialogRef<DeleteUserComponent>);
  readonly dialogData = inject(MAT_DIALOG_DATA);

  busy: WritableSignal<boolean> = signal(true);

  user: User | undefined = undefined;
  isUserAdmin: boolean = false;
  isOwnUser: boolean = false;

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

    this.isUserAdmin = this.authService.computePermissionsSignal(permissions => permissions.includes("ADMIN"))();
    this.isOwnUser = this.authService.computeUserSignal(user => user?.id === this.user?.id)();

    this.busy.set(false);
  }

  canEdit() {
    return this.isUserAdmin || this.isOwnUser;
  }

  canDeleteUser() {
    return this.user != null
      && !this.busy()
      && !this.submitting()
      && this.canEdit();
  }

  deleteUser() {
    if (!this.canDeleteUser()) {
      return;
    }

    this.submitting.set(true);

    this.usersService.deleteUser(this.user?.id!)
      .subscribe({
        next: result => {
          this.submitting.set(false);
          this.notificationsService.pushNotification(Notification("SUCCESS", "Successfully deleted user"));

          if (this.isOwnUser) {
            this.authService.clearSession();
          }

          this.close();
        },
        error: (err: Error) => {
          this.notificationsService.pushNotification(Notification("ERROR", "Failed to delete user"));
          this.submitting.set(false);
        }
      });
  }

  close() {
    this.busy.set(false);
    this.dialogRef.close();
  }
}

