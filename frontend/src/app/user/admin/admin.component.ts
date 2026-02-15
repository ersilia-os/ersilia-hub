import { Component, computed, inject, OnDestroy, OnInit, signal, Signal, TrackByFunction, WritableSignal } from '@angular/core';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialog } from '@angular/material/dialog';
import { ErsiliaLoaderComponent } from '../../ersilia-loader/ersilia-loader.component';
import { UsersService } from '../../../services/users.service';
import { User, UsersFilter } from '../../../objects/user';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { FormsModule } from "@angular/forms";
import { UserInfoPopupComponent } from '../info-popup/info-popup.component';
import { DeleteUserComponent } from '../delete-user/delete-user.component';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-user-admin',
  standalone: true,
  imports: [
    MatButtonModule, MatTableModule, CommonModule, MatIconModule, MatProgressBarModule, ErsiliaLoaderComponent,
    MatFormFieldModule, MatSelectModule, MatInputModule, FormsModule
  ],
  templateUrl: './admin.component.html',
  styleUrl: './admin.component.scss'
})
export class UserAdminComponent implements OnInit {
  private activatedRoute = inject(ActivatedRoute);
  private userAdminService = inject(UsersService);
  private usersFilters: UsersFilter = {};

  readonly dialog = inject(MatDialog);

  users: WritableSignal<User[]> = signal([]);
  loading: WritableSignal<boolean> = signal(false);
  autoOpenUserDialogFor: WritableSignal<string | undefined> = signal(undefined);

  displayedColumns: string[] = ['username', 'first_name', 'last_name', 'email', 'actions'];
  columnHeaders: { [column: string]: string } = {
    username: 'Username',
    first_name: 'First Name',
    last_name: 'Last Name',
    email: 'Email',
    actions: ''
  };

  constructor() {
  }

  get filterUsername(): string | undefined {
    return this.usersFilters.username;
  }

  set filterUsername(value: string | undefined) {
    this.usersFilters.username = value;

    this.load();
  }

  get filterUsernamePrefix(): string | undefined {
    return this.usersFilters.username_prefix;
  }

  set filterUsernamePrefix(value: string | undefined) {
    this.usersFilters.username_prefix = value;

    this.load();
  }

  get filterFirstnamePrefix(): string | undefined {
    return this.usersFilters.firstname_prefix;
  }

  set filterFirstnamePrefix(value: string | undefined) {
    this.usersFilters.firstname_prefix = value;

    this.load();
  }

  get filterLastnamePrefix(): string | undefined {
    return this.usersFilters.lastname_prefix;
  }

  set filterLastnamePrefix(value: string | undefined) {
    this.usersFilters.lastname_prefix = value;

    this.load();
  }

  get filterEmailPrefix(): string | undefined {
    return this.usersFilters.email_prefix;
  }

  set filterEmailPrefix(value: string | undefined) {
    this.usersFilters.email_prefix = value;

    this.load();
  }

  ngOnInit(): void {
    try {
      let dialogUsername: string | undefined;

      this.activatedRoute.queryParams.subscribe(params => {
        if (params["username"] != null) {
          dialogUsername = params["username"];
        }
      });

      if (dialogUsername != null) {
        this.autoOpenUserDialogFor.set(dialogUsername);
        this.usersFilters = {
          username: dialogUsername
        };
      }

      this.load();
    } catch {
      // ignore
      this.load();
    }

  }

  load() {
    if (this.loading()) {
      return;
    }

    this.loading.set(true);

    try {
      this.userAdminService.filterUsers(this.usersFilters)
        .subscribe(users => {
          this.users.set(users);
          this.autoOpenUserDialog();
          this.loading.set(false);
        });
    } catch (e) {
      this.loading.set(false);
    }
  }

  tableTrackBy: TrackByFunction<User> = (index: number, item: User) => {
    return `${item.username}_${item.last_updated}`;
  };

  autoOpenUserDialog() {
    if (this.autoOpenUserDialogFor() == undefined) {
      return;
    }

    const dialogUser = this.users().find(user => user.username === this.autoOpenUserDialogFor());

    if (dialogUser != null) {
      this.openUserDialog(dialogUser);
    }
  }

  openUserDialog(user: User) {
    if (this.autoOpenUserDialogFor() != undefined) {
      this.autoOpenUserDialogFor.set(undefined);
    }

    this.dialog.open(UserInfoPopupComponent, {
      enterAnimationDuration: '300ms',
      exitAnimationDuration: '300ms',
      panelClass: 'dialog-panel',
      data: user,
    });
  }

  openDeleteDialog(user: User) {
    this.dialog.open(DeleteUserComponent, {
      enterAnimationDuration: '300ms',
      exitAnimationDuration: '300ms',
      panelClass: 'dialog-panel',
      data: user,
    });
  }
}
