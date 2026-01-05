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
import { ErrorStateMatcher } from '@angular/material/core';

@Component({
  standalone: true,
  imports: [
    MatButtonModule, CommonModule, MatIconModule, MatProgressBarModule,
    MatDialogActions, MatDialogClose, MatDialogTitle, MatDialogContent,
    MatFormFieldModule, MatSelectModule, FormsModule, MatInputModule, ErsiliaLoaderComponent,
    ReactiveFormsModule, MatTooltipModule, MatCheckboxModule
  ],
  templateUrl: './update-user-password.component.html',
  styleUrl: './update-user-password.component.scss'
})
export class UpdateUserPasswordComponent implements OnInit {
  readonly dialogRef = inject(MatDialogRef<UpdateUserPasswordComponent>);
  readonly dialogData = inject(MAT_DIALOG_DATA);

  busy: WritableSignal<boolean> = signal(true);

  user: User | undefined = undefined;
  isOwnUser: boolean = true;
  isUserAdmin: boolean = false;

  private usersService = inject(UsersService);
  private authService = inject(AuthService);
  private notificationsService = inject(NotificationsService);

  submitting: WritableSignal<boolean> = signal(false);

  private passwordRegex = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[a-zA-Z]).{16,}$/;

  updateCurrentPasswordControl = new FormControl('', [Validators.required, (control) => passwordFormControl(control, this.passwordRegex)]);
  updateNewPasswordControl = new FormControl('', [Validators.required, (control) => passwordFormControl(control, this.passwordRegex)]);
  updateNewPasswordConfirmationControl = new FormControl('', [Validators.required, (control) => passwordFormControl(control, this.passwordRegex, this.updateNewPasswordControl.getRawValue())]);
  formControlErrorStateMatcher = new MyErrorStateMatcher()

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

  isPasswordUpdateFormValid(): boolean {
    return (
      !this.isOwnUser
      || this.updateCurrentPasswordControl.valid
    ) && this.updateNewPasswordControl.valid
      && this.updateNewPasswordConfirmationControl.valid;
  }

  clearPasswordUpdateForm() {
    this.updateCurrentPasswordControl.reset();
    this.updateNewPasswordControl.reset();
    this.updateNewPasswordConfirmationControl.reset();
  }

  canSubmitPasswordUpdate(): boolean {
    return this.canSubmit()
      && this.isPasswordUpdateFormValid()
  }

  updatePassword() {
    if (!this.canSubmitPasswordUpdate()) {
      return;
    }

    this.submitting.set(true);

    this.usersService.updateUserPassword(
      this.user?.id!,
      this.updateNewPasswordControl.getRawValue()!,
      this.isOwnUser ? this.updateCurrentPasswordControl.getRawValue()! : undefined,
      !this.isOwnUser).subscribe({
        next: result => {
          this.submitting.set(false);
          this.notificationsService.pushNotification(Notification("SUCCESS", "Successfully updated user password"));
          this.close();
        },
        error: (err: Error) => {
          this.notificationsService.pushNotification(Notification("ERROR", "Failed to update user password"));
          this.submitting.set(false);
        }
      })
  }

  close() {
    this.clearPasswordUpdateForm();
    this.busy.set(false);
    this.dialogRef.close();
  }
}

export class MyErrorStateMatcher implements ErrorStateMatcher {
  isErrorState(control: FormControl | null, form: FormGroupDirective | NgForm | null): boolean {
    const isSubmitted = form && form.submitted;
    return !!(control && control.invalid && (control.dirty || control.touched || isSubmitted));
  }
}

function passwordFormControl(control: AbstractControl, passwordRegex: RegExp, comparison?: string | null) {
  if (!control.dirty) {
    return null;
  }

  const value = control.getRawValue();

  if (value == null || value.length < 3) {
    return {
      'validation': 'Invalid password'
    }
  }

  if (value.match(passwordRegex) == null) {
    return {
      'validation': `Password must match regex [${passwordRegex}]`
    }
  }

  if (comparison != undefined && value !== comparison) {
    return {
      'validation': 'Does not match Password field'
    }
  }

  return null;
}
