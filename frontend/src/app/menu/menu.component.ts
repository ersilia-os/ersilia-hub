import { CommonModule } from "@angular/common";
import { Component, EventEmitter, inject, Input, OnInit, Output } from "@angular/core";
import { MatIconModule } from "@angular/material/icon";
import { AppPermissions } from "../../objects/auth";
import { Router } from "@angular/router";


@Component({
    selector: 'app-menu',
    standalone: true,
    imports: [CommonModule, MatIconModule],
    templateUrl: './menu.component.html',
    styleUrl: './menu.component.scss'
})
export class MenuComponent implements OnInit {
    private router = inject(Router);

    @Input() appPermissions: AppPermissions | undefined;

    @Output() exit: EventEmitter<void> = new EventEmitter();

    menu: MenuItem[] = [];

    ngOnInit() {
        this.menu = buildMenu(this.appPermissions!);
    }

    activateMenuItem(item: MenuItem) {
        this.router.navigate([item.link])
            .then(success => {
                this.hideMenu()
            })
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
        link: ''
    });

    if (permissions.canViewStats) {
        menu.push({
            text: 'Stats',
            icon: 'analytics',
            link: 'stats'
        });
    }

    if (permissions.canManageInstances) {
        menu.push({
            text: 'Instances',
            icon: 'developer_board',
            link: 'instances'
        });
        menu.push({
            text: 'Recommendations',
            icon: 'published_with_changes',
            link: 'recommendations'
        });
        menu.push({
            text: 'Models',
            icon: 'settings',
            link: 'models'
        })
        // model management = database_upload
    }

    return menu;
}