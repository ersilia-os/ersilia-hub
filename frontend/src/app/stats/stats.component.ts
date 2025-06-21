import { CommonModule } from "@angular/common";
import { Component, inject, OnInit, signal, TrackByFunction, WritableSignal } from "@angular/core";
import { MatIconModule } from "@angular/material/icon";
import { RequestStatsService } from "../../services/request-stats.service";
import { WorkRequestStats, WorkRequestStatsFilterData, WorkRequestStatsFilters } from "../../objects/request-stats";
import { NotificationsService, Notification } from "../notifications/notifications.service";
import { MatFormFieldModule } from "@angular/material/form-field";
import { MatSelectModule } from "@angular/material/select";
import { FormsModule } from "@angular/forms";
import { MatInputModule } from "@angular/material/input";
import { ErsiliaLoaderComponent } from "../ersilia-loader/ersilia-loader.component";
import { MatTableModule } from "@angular/material/table";
import { DataTablesModule } from "angular-datatables";
import { MatDatepickerInputEvent, MatDatepickerModule } from '@angular/material/datepicker';
import { provideNativeDateAdapter } from "@angular/material/core";

const DAY_IN_MILLIS = 86400000;

@Component({
    selector: 'app-stats',
    standalone: true,
    imports: [
        CommonModule, MatIconModule, MatFormFieldModule, MatTableModule,
        MatSelectModule, FormsModule, MatInputModule, ErsiliaLoaderComponent, DataTablesModule,
        MatDatepickerModule
    ],
    providers: [provideNativeDateAdapter()],
    templateUrl: './stats.component.html',
    styleUrl: './stats.component.scss'
})
export class StatsComponent implements OnInit {

    private statsService = inject(RequestStatsService);
    private notificationsService = inject(NotificationsService);

    loading: WritableSignal<boolean> = signal(true);
    filterData: WritableSignal<WorkRequestStatsFilterData> = signal(
        {
            model_ids: [],
            group_by: ["ModelId"],
        }
    );

    private _requestDateFrom: Date = new Date(new Date().setHours(0, 0, 0) - (7 * DAY_IN_MILLIS));

    get requestDateFrom(): Date {
        return this._requestDateFrom;
    }

    set requestDateFrom(date: Date) {
        this._requestDateFrom = date;
        this.onFiltersUpdated();
    }

    private _requestDateTo: Date = new Date(new Date().setHours(23, 59, 59));

    get requestDateTo(): Date {
        return this._requestDateTo;
    }

    set requestDateTo(date: Date) {
        this._requestDateTo = date;
        this.onFiltersUpdated();
    }

    private _groupBy: string[] = ["ModelId"];

    get groupBy(): string[] {
        return this._groupBy;
    }

    set groupBy(groupBy: string[]) {
        this._groupBy = groupBy;
        this.filters.group_by = groupBy;

        this.onFiltersUpdated();
    }

    filters: WorkRequestStatsFilters = {};

    private _displaySelection: 'Totals' | 'Success' | 'Failed' = 'Totals';

    get displaySelection(): 'Totals' | 'Success' | 'Failed' {
        return this._displaySelection;
    }

    set displaySelection(selection: 'Totals' | 'Success' | 'Failed') {
        this._displaySelection = selection;

        this.onFiltersUpdated();
    }

    stats: WritableSignal<WorkRequestStats[]> = signal([]);

    commonColumns: string[] = [
        'model_id',
    ];

    totalColumns: string[] = [
        'total_count',
        'success_count',
        'failed_count',
        'total_all_request_start_time',
        'max_all_request_start_time',
        'min_all_request_start_time',
        'avg_all_request_start_time',
        'total_all_request_time',
        'max_all_request_time',
        'min_all_request_time',
        'avg_all_request_time',
        'total_all_job_execution_time',
        'max_all_job_execution_time',
        'min_all_job_execution_time',
        'avg_all_job_execution_time',
    ];

    successColumns: string[] = [
        'success_count',
        'total_success_request_start_time',
        'max_success_request_start_time',
        'min_success_request_start_time',
        'avg_success_request_start_time',
        'total_success_request_time',
        'max_success_request_time',
        'min_success_request_time',
        'avg_success_request_time',
        'total_success_job_execution_time',
        'max_success_job_execution_time',
        'min_success_job_execution_time',
        'avg_success_job_execution_time',
    ];

    failedColumns: string[] = [
        'failed_count',
        'total_failed_request_start_time',
        'max_failed_request_start_time',
        'min_failed_request_start_time',
        'avg_failed_request_start_time',
        'total_failed_request_time',
        'max_failed_request_time',
        'min_failed_request_time',
        'avg_failed_request_time',
        'total_failed_job_execution_time',
        'max_failed_job_execution_time',
        'min_failed_job_execution_time',
        'avg_failed_job_execution_time',
    ];

    displayedColumns: string[] = [
    ];

    columnHeaders: { [column: string]: string } = {
        model_id: 'model_id',
        input_size: 'input_size',
        total_count: 'total_count',
        success_count: 'success_count',
        failed_count: 'failed_count',
        total_all_request_start_time: 'total_all_request_start_time',
        max_all_request_start_time: 'max_all_request_start_time',
        min_all_request_start_time: 'min_all_request_start_time',
        avg_all_request_start_time: 'avg_all_request_start_time',
        total_all_request_time: 'total_all_request_time',
        max_all_request_time: 'max_all_request_time',
        min_all_request_time: 'min_all_request_time',
        avg_all_request_time: 'avg_all_request_time',
        total_all_job_execution_time: 'total_all_job_execution_time',
        max_all_job_execution_time: 'max_all_job_execution_time',
        min_all_job_execution_time: 'min_all_job_execution_time',
        avg_all_job_execution_time: 'avg_all_job_execution_time',
        total_success_request_start_time: 'total_success_request_start_time',
        max_success_request_start_time: 'max_success_request_start_time',
        min_success_request_start_time: 'min_success_request_start_time',
        avg_success_request_start_time: 'avg_success_request_start_time',
        total_success_request_time: 'total_success_request_time',
        max_success_request_time: 'max_success_request_time',
        min_success_request_time: 'min_success_request_time',
        avg_success_request_time: 'avg_success_request_time',
        total_success_job_execution_time: 'total_success_job_execution_time',
        max_success_job_execution_time: 'max_success_job_execution_time',
        min_success_job_execution_time: 'min_success_job_execution_time',
        avg_success_job_execution_time: 'avg_success_job_execution_time',
        total_failed_request_start_time: 'total_failed_request_start_time',
        max_failed_request_start_time: 'max_failed_request_start_time',
        min_failed_request_start_time: 'min_failed_request_start_time',
        avg_failed_request_start_time: 'avg_failed_request_start_time',
        total_failed_request_time: 'total_failed_request_time',
        max_failed_request_time: 'max_failed_request_time',
        min_failed_request_time: 'min_failed_request_time',
        avg_failed_request_time: 'avg_failed_request_time',
        total_failed_job_execution_time: 'total_failed_job_execution_time',
        max_failed_job_execution_time: 'max_failed_job_execution_time',
        min_failed_job_execution_time: 'min_failed_job_execution_time',
        avg_failed_job_execution_time: 'avg_failed_job_execution_time',
    };

    ngOnInit(): void {
        this.loading.set(true);
        this.onFiltersUpdated();

        this.statsService.loadRequestStatsFilterData()
            .subscribe({
                next: filterData => {
                    this.filterData.set(filterData);
                    this.filters.model_ids = [...filterData.model_ids]
                    this.loading.set(false);

                    this.loadStats();
                },
                error: err => {
                    this.notificationsService.pushNotification(Notification('ERROR', `Failed to load filter data`));
                    this.loading.set(false);
                }
            });
    }

    tableTrackBy: TrackByFunction<WorkRequestStats> = (index: number, item: WorkRequestStats) => {
        if (this.filters.group_by == null || this.filters.group_by.length <= 1) {
            return `${item.model_id}`;
        } else {
            // TODO: add all the group by fields
            return `${item.model_id}_${item.input_size}`;
        }
    };

    isStickyColumn(column: string): boolean {
        if (column === 'model_id') {
            return true;
        } else if (column === 'input_size' && this.filters.group_by != null && this.filters.group_by.includes("InputSize")) {
            return true;
        }

        return false;
    }

    onFiltersUpdated() {
        let newColumns = [...this.commonColumns];

        if (this.filters.group_by != null && this.filters.group_by.includes("InputSize")) {
            newColumns.push("input_size");
        }

        if (this.displaySelection === 'Totals') {
            newColumns = newColumns.concat(this.totalColumns);
        } else if (this.displaySelection === 'Success') {
            newColumns = newColumns.concat(this.successColumns);
        } else if (this.displaySelection === 'Failed') {
            newColumns = newColumns.concat(this.failedColumns);
        }

        this.displayedColumns = newColumns;

        this.filters.request_date_from = new Date(this.requestDateFrom.setHours(0, 0, 0)).toISOString();
        this.filters.request_date_to = new Date(this.requestDateTo.setHours(23, 59, 59)).toISOString();
    }

    fromDateChange(eventType: string, event: MatDatepickerInputEvent<Date>) {
        if (event == null || event.value == null) {
            this.filters.request_date_from = undefined;

            return;
        }

        this.filters.request_date_from = event.value.toISOString();
    }

    toDateChange(eventType: string, event: MatDatepickerInputEvent<Date>) {
        if (event == null || event.value == null) {
            this.filters.request_date_to = undefined;

            return;
        }

        this.filters.request_date_to = event.value.toISOString();
    }

    loadStats() {
        if (this.loading()) {
            return;
        }

        this.loading.set(true);

        this.statsService.loadRequestStats(this.filters)
            .subscribe({
                next: stats => {
                    this.stats.set(stats.stats);
                    this.loading.set(false);
                },
                error: err => {
                    this.notificationsService.pushNotification(Notification('ERROR', `Failed to load stats`));
                    this.loading.set(false);
                }
            })
    }

    downloadCsv() {
        const a = document.createElement('a');
        let objectUrl: string | undefined = undefined;
        let csv: string[] = [this.displayedColumns.map(c => `"${c}"`).join(",")];

        for (const entry of this.stats()) {
            const entryObj = {} as { [key: string]: any };

            for (const e of Object.entries(entry)) {
                entryObj[e[0]] = e[1];
            }

            csv.push(
                this.displayedColumns.map(c => {
                    if (c === 'model_id') {
                        return `"${entryObj[c]}"`;
                    } else {
                        return `${entryObj[c]}`;
                    }
                }).join(",")
            );
        }

        a.href = URL.createObjectURL(new Blob([csv.join("\n")], {
            type: "text/csv",
        }));

        a.download = 'ersiliahub_stats.csv';
        a.click();
        URL.revokeObjectURL(objectUrl!);
    }
}
