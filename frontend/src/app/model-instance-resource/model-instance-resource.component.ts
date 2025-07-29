import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import { ModelInstance } from '../../objects/instance';
import { ResourceProfileConfig, ResourceProfileId, ResourceProfileState } from '../../objects/recommendations';

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
    recommendedProfile: ResourceProfileConfig | undefined;

    ngClass: { [key: string]: boolean } = {};
    fillGradient: string | undefined;
    indicatorPosition: string | undefined;
    indicatorWidth: string | undefined;
    indicatorPercentageClass: { [key: string]: boolean } = {}

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
                    this.recommendedProfile = this.instance.resource_recommendations.cpu_min.recommended_profile;
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
                    this.recommendedProfile = this.instance.resource_recommendations.cpu_min.recommended_profile;
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
                    this.recommendedProfile = this.instance.resource_recommendations.cpu_min.recommended_profile;
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
                    this.recommendedProfile = this.instance.resource_recommendations.cpu_min.recommended_profile;
                    this.currentProfileState = this.instance.resource_recommendations.memory_min.current_profile_state.state;
                }

                break;
        }

        if (this.currentProfileState != null) {
            this.ngClass[`profile-state-${this.currentProfileState.toLowerCase()}`] = true;

            if ((this.usagePercentage ?? 0) >= 45) {
                this.indicatorPercentageClass['profile-state-black'] = true;
            } else {
                this.indicatorPercentageClass[`profile-state-${this.currentProfileState.toLowerCase()}`] = true;
            }
        }

        this.setFill();
    }

    setFill() {
        if ((this.usagePercentage ?? 0) >= 100) {
            this.indicatorPosition = '0px';
            this.indicatorWidth = '0px';
        } else {
            let indicatorPositionValue = 150 * ((this.usagePercentage ?? 0) / 100);
            this.indicatorPosition = `${indicatorPositionValue}px`;
            this.indicatorWidth = `${150 - indicatorPositionValue}px`;
        }

        if (this.instance == null || this.instance.resource_recommendations == null || this.recommendedProfile == null) {
            this.fillGradient = 'linear-gradient(90deg, #f79e3a 25%, #31ec5a 65%, #f79e3a 90%)';
            return;
        }

        let gradientPercentages = [
            this.recommendedProfile?.min - 20,
            this.recommendedProfile?.min - 10,
            this.recommendedProfile?.min,
            this.recommendedProfile?.max,
            this.recommendedProfile?.max + 10,
            this.recommendedProfile?.max + 20
        ];
        this.fillGradient = `linear-gradient(90deg, #f79e3a ${gradientPercentages[0]}%, #f8f84a ${gradientPercentages[1]}%, #31ec5a ${gradientPercentages[2]}%, #f8f84a ${gradientPercentages[3]}%, #f79e3a ${gradientPercentages[4]}%)`
    }
}