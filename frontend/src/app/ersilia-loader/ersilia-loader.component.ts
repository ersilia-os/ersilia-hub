import { CommonModule } from '@angular/common';
import { Component, HostBinding, Input, OnInit } from '@angular/core';

@Component({
    standalone: true,
    imports: [
        CommonModule
    ],
    templateUrl: './ersilia-loader.component.html',
    styleUrl: './ersilia-loader.component.scss',
    selector: 'ersilia-loader'
})
export class ErsiliaLoaderComponent implements OnInit {
    @HostBinding('class.animate')
    @Input() animate: boolean = true;

    @HostBinding('class.scale')
    @Input() scale: 'small' | 'medium' | 'large' = 'small';

    @Input() colour: string | undefined;
    @Input() splash: boolean = false;

    ngClass: { [key: string]: boolean } = {};

    debug = false;

    ngOnInit() {
        if (this.debug) {
            this.colour = "red";
        }

        if (this.animate) {
            this.ngClass['animate'] = true;
        } else {
            this.ngClass['static'] = true;
        }

        if (this.scale === 'small') {
            this.ngClass['small'] = true;
        } else if (this.scale === 'medium') {
            this.ngClass['medium'] = true;
        } else {
            this.ngClass['large'] = true;
        }

        if (this.splash) {
            this.ngClass['splash-animation'] = true;
        }
    }
}
