import { CommonModule } from "@angular/common";
import { Component, EventEmitter, Input, OnInit, Output } from "@angular/core";
import { MatIconModule } from "@angular/material/icon";
import { AppPermissions } from "../../objects/auth";


@Component({
    selector: 'app-menu',
    standalone: true,
    imports: [CommonModule, MatIconModule],
    templateUrl: './menu.component.html',
    styleUrl: './menu.component.scss'
})
export class MenuComponent implements OnInit {

    @Input() appPermissions: AppPermissions | undefined;

    @Output() exit: EventEmitter<void> = new EventEmitter();

    menu: MenuItem[] = [];

    ngOnInit() {
        this.menu = buildMenu(this.appPermissions!);
    }

    activateMenuItem(item: MenuItem) {
        // TODO: navigate?
    }

    hideMenu() {
        this.exit.emit();
    }
}

interface MenuItem {
    text: string;
    icon: string;
    link: string;
}

function buildMenu(permissions: AppPermissions): MenuItem[] {
    let menu: MenuItem[] = [];

    if (!permissions.canViewMenu) {
        return menu;
    }

    menu.push({
        text: 'Evaluations',
        icon: 'science',
        link: '/'
    });

    if (permissions.canViewStats) {
        menu.push({
            text: 'Stats',
            icon: 'analytics',
            link: '/stats'
        });
    }

    return menu;
}