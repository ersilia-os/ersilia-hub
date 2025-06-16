import { CommonModule } from "@angular/common";
import { Component, EventEmitter, Input, OnInit, Output } from "@angular/core";
import { MatIconModule } from "@angular/material/icon";


@Component({
    selector: 'app-stats',
    standalone: true,
    imports: [CommonModule, MatIconModule],
    templateUrl: './stats.component.html',
    styleUrl: './stats.component.scss'
})
export class StatsComponent {


}
