import { Component, inject, OnDestroy, signal, Signal, TrackByFunction, WritableSignal } from '@angular/core';
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
export class UserAdminComponent {

  private userAdminService = inject(UsersService);
  private usersFilters: UsersFilter = {

  };

  readonly dialog = inject(MatDialog);

  users: WritableSignal<User[]> = signal([]);
  loading: WritableSignal<boolean> = signal(false);

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

  load() {
    if (this.loading()) {
      return;
    }

    this.loading.set(true);

    try {
      this.userAdminService.filterUsers(this.usersFilters)
        .subscribe(users => {
          this.users.set(users);
          this.loading.set(false);
        });
    } catch (e) {
      this.loading.set(false);
    }
  }

  tableTrackBy: TrackByFunction<User> = (index: number, item: User) => {
    return `${item.username}_${item.last_updated}`;
  };

  openUserDialog(user: User) {
    this.dialog.open(UserInfoPopupComponent, {
      enterAnimationDuration: '300ms',
      exitAnimationDuration: '300ms',
      panelClass: 'dialog-panel',
      data: user,
    });
  }

  openDeleteDialog(user: User) {
    // TODO: check if there is a callback to trigger on close ??

    // this.dialog.open(UserDeleteDialogComponent, {
    //   enterAnimationDuration: '300ms',
    //   exitAnimationDuration: '300ms',
    //   panelClass: 'dialog-panel',
    //   data: user,
    // });
  }
}
