import { CommonModule } from "@angular/common";
import { Component, inject, OnInit, signal, WritableSignal } from "@angular/core";
import { MatIconModule } from "@angular/material/icon";
import { RequestStatsService } from "../../services/request-stats.service";
import { WorkRequestStatsFilterData, WorkRequestStatsFilters, WorkRequestStatsList } from "../../objects/request-stats";
import { NotificationsService, Notification } from "../notifications/notifications.service";
import { MatFormFieldModule } from "@angular/material/form-field";
import { MatSelectModule } from "@angular/material/select";
import { FormsModule } from "@angular/forms";
import { MatInputModule } from "@angular/material/input";
import { ErsiliaLoaderComponent } from "../ersilia-loader/ersilia-loader.component";


@Component({
    selector: 'app-stats',
    standalone: true,
    imports: [
        CommonModule, MatIconModule, MatFormFieldModule,
        MatSelectModule, FormsModule, MatInputModule, ErsiliaLoaderComponent],
    templateUrl: './stats.component.html',
    styleUrl: './stats.component.scss'
})
export class StatsComponent implements OnInit {

    private statsService = inject(RequestStatsService);
    private notificationsService = inject(NotificationsService);

    loading: WritableSignal<boolean> = signal(true);
    filterData: WritableSignal<WorkRequestStatsFilterData> = signal({ model_ids: [] });

    filters: WorkRequestStatsFilters = {};

    stats: WritableSignal<WorkRequestStatsList> = signal({ stats: [] });

    ngOnInit(): void {
        this.loading.set(true);

        this.statsService.loadRequestStatsFilterData()
            .subscribe({
                next: filterData => {
                    this.filterData.set(filterData);
                    this.filters.model_ids = [...filterData.model_ids]
                    this.loading.set(false);
                },
                error: err => {
                    this.notificationsService.pushNotification(Notification('ERROR', `Failed to load filter data`));
                    this.loading.set(false);
                }
            })
    }

    loadStats() {
        if (this.loading()) {
            return;
        }

        this.loading.set(true);

        this.statsService.loadRequestStats(this.filters)
            .subscribe({
                next: stats => {
                    this.stats.set(stats);
                    this.loading.set(false);
                },
                error: err => {
                    this.notificationsService.pushNotification(Notification('ERROR', `Failed to load stats`));
                    this.loading.set(false);
                }
            })
    }
}
