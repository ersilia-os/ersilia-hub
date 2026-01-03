import { CommonModule } from "@angular/common";
import { Component, inject, OnInit, Signal, signal, WritableSignal } from "@angular/core";
import { MatButtonModule } from "@angular/material/button";
import { MatIconModule } from "@angular/material/icon";
import { ErsiliaLoaderComponent } from "../ersilia-loader/ersilia-loader.component";
import { AuthService } from "../../services/auth.service";
import { NotificationsService, Notification } from "../notifications/notifications.service";
import { MatFormFieldModule } from "@angular/material/form-field";
import { FormControl, FormGroupDirective, FormsModule, NgForm, ReactiveFormsModule, Validators } from "@angular/forms";
import { MatInputModule } from "@angular/material/input";
import { User } from "../../objects/user";
import { ErrorStateMatcher } from "@angular/material/core";
import { generateGuid } from "../utils/random";
import { MatTooltipModule } from "@angular/material/tooltip";
import { Clipboard } from '@angular/cdk/clipboard';

@Component({
  standalone: true,
  imports: [
    MatButtonModule, CommonModule, MatIconModule, ErsiliaLoaderComponent,
    MatFormFieldModule, MatInputModule, FormsModule, ReactiveFormsModule, MatTooltipModule
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
  selector: 'login'
})
export class LoginComponent implements OnInit {

  busy: WritableSignal<boolean> = signal(false);
  private authService = inject(AuthService);
  private notificationsService = inject(NotificationsService);
  private clipboard = inject(Clipboard);

  private lastAnonSessionId: Signal<string | undefined>;

  constructor() {
    this.lastAnonSessionId = this.authService.getLastAnonSessionId();
  }

  loginFormState: 'ANON_LOGIN' | 'SIGN_UP' | 'LOGIN' = 'ANON_LOGIN';

  // anon login form
  anonSessionIdControl = new FormControl('', [Validators.required, (control) => {
    if (!control.dirty) {
      return null;
    }

    const value = control.getRawValue();

    if (value == null || value.length < 36) {
      return {
        'validation': 'Invalid Session Id'
      }
    }

    return null;
  }]);

  // login form
  private _loginUsername: string | undefined;
  get loginUsername(): string | undefined {
    return this._loginUsername;
  }

  set loginUsername(username: string | undefined) {
    // TODO: validation
    this._loginUsername = username;
  }

  private _loginPassword: string | undefined;
  get loginPassword(): string | undefined {
    return this._loginPassword;
  }

  set loginPassword(password: string | undefined) {
    // TODO: validation
    this._loginPassword = password;
  }

  // signup form
  private signupPasswordRegex = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[a-zA-Z]).{16,}$/;

  signupUsernameControl = new FormControl('', [Validators.required, (control) => {
    if (!control.dirty) {
      return null;
    }

    const value = control.getRawValue();

    if (value == null || value.length < 3) {
      return {
        'validation': 'Invalid Username'
      }
    }

    return null;
  }]);

  signupFirstNameControl = new FormControl('', [Validators.required, (control) => {
    if (!control.dirty) {
      return null;
    }

    const value = control.getRawValue();

    if (value == null || value.length < 3) {
      return {
        'validation': 'Invalid First Name'
      }
    }

    return null;
  }]);

  signupLastNameControl = new FormControl('', [Validators.required, (control) => {
    if (!control.dirty) {
      return null;
    }

    const value = control.getRawValue();

    if (value == null || value.length < 3) {
      return {
        'validation': 'Invalid Last Name'
      }
    }

    return null;
  }]);

  signupEmailControl = new FormControl('', [Validators.email]);

  signupPasswordControl = new FormControl('', [Validators.required, (control) => {
    if (!control.dirty) {
      return null;
    }

    const value = control.getRawValue();

    if (value == null || value.length < 3) {
      return {
        'validation': 'Invalid password'
      }
    }

    if (value.match(this.signupPasswordRegex) == null) {
      return {
        'validation': `Password must match regex [${this.signupPasswordRegex}]`
      }
    }

    return null;
  }]);

  signupConfirmationPasswordControl = new FormControl('', [Validators.required, (control) => {
    if (!control.dirty) {
      return null;
    }

    const value = control.getRawValue();

    if (value == null || value.length < 3) {
      return {
        'validation': 'Invalid Confirmation Password'
      }
    }

    if (value !== this.signupPasswordControl.getRawValue()) {
      return {
        'validation': 'Does not match Password field'
      }
    }

    return null;
  }]);

  formControlErrorStateMatcher = new MyErrorStateMatcher()

  ngOnInit() {
    if (this.lastAnonSessionId() != null) {
      this.anonSessionIdControl.setValue(this.lastAnonSessionId()!);
    }
  }

  // anon login functions
  canAnonLogin() {
    return this.anonSessionIdControl.valid
  }

  anonLogin() {
    if (!this.canAnonLogin()) {
      return;
    }

    this.busy.set(true);
    this.authService.anonLogin(this.anonSessionIdControl.getRawValue()!)
      .subscribe({
        next: _ => {
          this.busy.set(false);
        },
        error: err => {
          this.notificationsService.pushNotification(Notification('ERROR', err));
          this.busy.set(false);
        }
      });
  }

  generateAnonSessionId() {
    if (this.busy()) {
      return;
    }

    this.anonSessionIdControl.setValue(generateGuid());
  }

  copyAnonSessionId() {
    if (!this.anonSessionIdControl.valid) {
      return;
    }

    if (this.clipboard.copy(this.anonSessionIdControl.getRawValue()!)) {
      this.notificationsService.pushNotification(Notification('SUCCESS', 'Session Id Copied'))
    } else {
      this.notificationsService.pushNotification(Notification('WARN', 'Failed to copy Session Id'))
    }
  }

  // login functions
  openLoginForm() {
    this.loginFormState = 'LOGIN';
  }

  canLogin() {
    return this._loginPassword != null && this._loginPassword.length > 10 && this._loginUsername != null && this._loginUsername.length > 3 && !this.busy();
  }

  userLogin() {
    if (!this.canLogin()) {
      return;
    }

    this.busy.set(true);
    this.authService.userLogin(this._loginUsername!, this._loginPassword!)
      .subscribe({
        next: _ => {
          this.busy.set(false);
        },
        error: err => {
          this.notificationsService.pushNotification(Notification('ERROR', err));
          this.busy.set(false);
        }
      });
  }

  clearLogin() {
    this._loginUsername = undefined;
    this._loginPassword = undefined;
  }

  cancelLogin() {
    this.loginFormState = 'ANON_LOGIN';
    this.clearLogin();
  }

  // sign up functions
  openSignUpForm() {
    this.loginFormState = 'SIGN_UP';
  }

  isSignUpFormValid(): boolean {
    return this.signupUsernameControl.valid
      && this.signupFirstNameControl.valid
      && this.signupLastNameControl.valid
      && this.signupEmailControl.valid
      && this.signupPasswordControl.valid
      && this.signupConfirmationPasswordControl.valid;
  }

  clearSignUpForm() {
    this.signupUsernameControl.reset();
    this.signupFirstNameControl.reset();
    this.signupLastNameControl.reset();
    this.signupEmailControl.reset();
    this.signupPasswordControl.reset();
    this.signupConfirmationPasswordControl.reset();
  }

  canSignUp(): boolean {
    return !this.busy() && this.isSignUpFormValid();
  }

  signUp() {
    if (!this.canSignUp()) {
      return;
    }

    this.busy.set(true);

    let user: User = {
      username: this.signupUsernameControl.getRawValue()!,
      first_name: this.signupFirstNameControl.getRawValue()!,
      last_name: this.signupLastNameControl.getRawValue()!,
      email: this.signupEmailControl.getRawValue()!
    };
    this.authService.signup(user, this.signupPasswordControl.getRawValue()!)
      .subscribe({
        next: result => {
          this.notificationsService.pushNotification(Notification('SUCCESS', 'Successfully Signed Up!'));
          this.loginFormState = 'LOGIN';
          this.clearSignUpForm();
          this.busy.set(false);
        },
        error: (err: Error) => {
          if (err.message == 'Username already in use') {
            this.signupUsernameControl.setErrors({ 'validation': err.message });
          }

          this.notificationsService.pushNotification(Notification('ERROR', 'Sign Up failed'));
          this.busy.set(false);
        }
      });
  }

  cancelSignUp() {
    this.loginFormState = 'LOGIN';
    this.clearSignUpForm();
  }
}

export class MyErrorStateMatcher implements ErrorStateMatcher {
  isErrorState(control: FormControl | null, form: FormGroupDirective | NgForm | null): boolean {
    const isSubmitted = form && form.submitted;
    return !!(control && control.invalid && (control.dirty || control.touched || isSubmitted));
  }
}
