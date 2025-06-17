import { Component, inject, OnDestroy, Signal, TrackByFunction } from '@angular/core';
import { Subscription, timer } from 'rxjs';
import { RequestsService } from '../../services/requests.service';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { Request, RequestFilters, RequestPayload, RequestStatus } from '../../objects/request';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialog } from '@angular/material/dialog';
import { RequestsCreateComponent } from '../request-create/request-create.component';
import { ErsiliaLoaderComponent } from '../ersilia-loader/ersilia-loader.component';
import { mapRequest, RequestDisplay } from '../../objects/request-view';
import { RequestViewComponent } from '../request-view/request-view.component';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-requests-list',
  standalone: true,
  imports: [MatButtonModule, MatTableModule, CommonModule, MatIconModule, MatProgressBarModule, ErsiliaLoaderComponent],
  templateUrl: './requests-list.component.html',
  styleUrl: './requests-list.component.scss'
})
export class RequestsListComponent implements OnDestroy {

  private requestService = inject(RequestsService);
  private refreshTimer$: Subscription | undefined;
  private requestFilters: RequestFilters = {
    limit: 25
  };

  readonly dialog = inject(MatDialog);
  private authService = inject(AuthService);
  private userId: Signal<string | undefined>;

  requests: Signal<RequestDisplay[]>;
  loading: Signal<boolean>;

  displayedColumns: string[] = ['id', 'model_id', 'request_date', 'request_status', 'actions'];
  columnHeaders: { [column: string]: string } = {
    id: 'id',
    model_id: 'Model Id',
    request_date: 'Request Date',
    request_status: 'Status',
    actions: ''
  };

  constructor() {
    this.userId = this.authService.computeUserSessionSignal(userSession => userSession == null ? undefined : userSession.userid);

    this.loading = this.requestService.computeRequestsLoadingSignal<boolean>(
      _loading => this.requests == null || (this.requests().length == 0 && _loading)
    );

    this.requests = this.requestService.computeRequestsSignal<RequestDisplay[]>(
      requests => requests.map(mapRequest)
    );

    this.refreshTimer$ = timer(0, 5000).subscribe(_ => {
      this.requestFilters.user_id = this.userId();
      this.requestService.loadRequests(this.requestFilters);
    });
  }

  ngOnDestroy() {
    this.refreshTimer$?.unsubscribe();
  }

  hasRequests(): boolean {
    return this.requests != null && this.requests().length > 0;
  }

  tableTrackBy: TrackByFunction<RequestDisplay> = (index: number, item: RequestDisplay) => {
    return `${item.id}_${item.last_updated}`;
  };

  openCreateRequestDialog(): void {
    if (this.dialog != null && this.dialog.openDialogs.length > 0) {
      return;
    }

    this.dialog.open(RequestsCreateComponent, {
      enterAnimationDuration: '300ms',
      exitAnimationDuration: '300ms',
      panelClass: 'dialog-panel'
    });
  }

  viewRequest(request: RequestDisplay) {
    this.dialog.open(RequestViewComponent, {
      enterAnimationDuration: '300ms',
      exitAnimationDuration: '300ms',
      panelClass: 'dialog-panel',
      data: request,
    });
  }
}
