import { CommonModule } from '@angular/common';
import { Component, HostBinding, Input, OnInit } from '@angular/core';
import { ModelInstance } from '../../objects/instance';
import { ResourceProfileId, ResourceProfileState } from '../../objects/recommendations';

@Component({
    standalone: true,
    imports: [
        CommonModule
    ],
    templateUrl: './model-instance-resource.component.html',
    styleUrl: './model-instance-resource.component.scss',
    selector: 'model-instance-resource'
})
export class ModelInstanceResourceComponent implements OnInit {
    @Input() instance: ModelInstance | undefined;
    @Input() resourceProfileId: ResourceProfileId | string | undefined;

    usageValue: number | undefined;
    allocationValue: number | undefined;
    usagePercentage: number | undefined;
    currentProfileState: ResourceProfileState | undefined;

    ngClass: { [key: string]: boolean } = {};

    ngOnInit() {
        if (this.instance == null || this.resourceProfileId == null) {
            return
        }

        if (this.instance.metrics == null && this.instance.resource_profile == null) {
            return;
        }

        switch (this.resourceProfileId) {
            case ResourceProfileId.CPU_MAX:
                if (this.instance.resource_profile == null) {
                    this.instance.metrics?.cpu_running_averages.max;
                    break;
                }

                this.usageValue = this.instance.resource_profile?.cpu.max_usage;
                this.usagePercentage = this.instance.resource_profile?.cpu.max_usage_percentage;
                this.allocationValue = this.instance.resource_profile?.cpu.max_allocatable;

                if (this.instance.resource_recommendations != null) {
                    this.currentProfileState = this.instance.resource_recommendations.cpu_max.current_profile_state.state;
                }

                break;

            case ResourceProfileId.CPU_MIN:
                if (this.instance.resource_profile == null) {
                    this.instance.metrics?.cpu_running_averages.min;
                    break;
                }

                this.usageValue = this.instance.resource_profile?.cpu.min_usage;
                this.usagePercentage = this.instance.resource_profile?.cpu.min_usage_percentage;
                this.allocationValue = this.instance.resource_profile?.cpu.min_allocatable;

                if (this.instance.resource_recommendations != null) {
                    this.currentProfileState = this.instance.resource_recommendations.cpu_min.current_profile_state.state;
                }

                break;

            case ResourceProfileId.MEMORY_MAX:
                if (this.instance.resource_profile == null) {
                    this.instance.metrics?.memory_running_averages.max;
                    break;
                }

                this.usageValue = this.instance.resource_profile?.memory.max_usage;
                this.usagePercentage = this.instance.resource_profile?.memory.max_usage_percentage;
                this.allocationValue = this.instance.resource_profile?.memory.max_allocatable;

                if (this.instance.resource_recommendations != null) {
                    this.currentProfileState = this.instance.resource_recommendations.memory_max.current_profile_state.state;
                }

                break;

            case ResourceProfileId.MEMORY_MIN:
                if (this.instance.resource_profile == null) {
                    this.instance.metrics?.memory_running_averages.min;
                    break;
                }

                this.usageValue = this.instance.resource_profile?.memory.min_usage;
                this.usagePercentage = this.instance.resource_profile?.memory.min_usage_percentage;
                this.allocationValue = this.instance.resource_profile?.memory.min_allocatable;

                if (this.instance.resource_recommendations != null) {
                    this.currentProfileState = this.instance.resource_recommendations.memory_min.current_profile_state.state;
                }

                break;
        }

        if (this.currentProfileState != null) {
            this.ngClass[`profile-state-${this.currentProfileState.toLowerCase()}`] = true;
        }
    }
}