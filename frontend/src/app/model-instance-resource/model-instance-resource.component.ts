import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import { ModelInstance } from '../../objects/instance';
import { ModelInstanceRecommendations, ResourceProfileConfig, ResourceProfileId, ResourceProfileState } from '../../objects/recommendations';

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
    @Input() recommendation: ModelInstanceRecommendations | undefined;
    @Input() resourceProfileId: ResourceProfileId | string | undefined;

    usageValue: number | undefined;
    allocationValue: number | undefined;
    usagePercentage: number | undefined;
    allocationPercentage: number | undefined;
    currentProfileState: ResourceProfileState | undefined;
    recommendedValue: number | undefined;
    recommendedProfile: ResourceProfileConfig | undefined;

    ngClass: { [key: string]: boolean } = {};
    indicatorClass: { [key: string]: boolean } = {};
    fillGradient: string | undefined;
    indicatorPosition: string | undefined;
    indicatorWidth: string | undefined;
    indicatorPercentageClass: { [key: string]: boolean } = {}
    recommendedIndicatorPosition: string | undefined;

    ngOnInit() {
        if ((this.instance == null && this.recommendation == null) || this.resourceProfileId == null) {
            return
        }

        if (this.recommendation == null) {
            this.applyInstance(this.instance!, this.resourceProfileId);
        } else {
            this.applyRecommendation(this.recommendation!, this.resourceProfileId);
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

    private applyInstance(instance: ModelInstance, resourceProfileId: ResourceProfileId | string) {
        switch (resourceProfileId) {
            case ResourceProfileId.CPU_MAX:
                if (instance.resource_profile == null) {
                    instance.metrics?.cpu_running_averages.max;
                    break;
                }

                this.usageValue = instance.resource_profile?.cpu.max_usage;
                this.usagePercentage = instance.resource_profile?.cpu.max_usage_percentage;
                this.allocationValue = instance.resource_profile?.cpu.max_allocatable;

                if (instance.resource_recommendations != null) {
                    this.recommendedProfile = instance.resource_recommendations.cpu_min.recommended_profile;
                    this.currentProfileState = instance.resource_recommendations.cpu_max.current_profile_state.state;
                }

                break;

            case ResourceProfileId.CPU_MIN:
                if (instance.resource_profile == null) {
                    instance.metrics?.cpu_running_averages.min;
                    break;
                }

                this.usageValue = instance.resource_profile?.cpu.min_usage;
                this.usagePercentage = instance.resource_profile?.cpu.min_usage_percentage;
                this.allocationValue = instance.resource_profile?.cpu.min_allocatable;

                if (instance.resource_recommendations != null) {
                    this.recommendedProfile = instance.resource_recommendations.cpu_min.recommended_profile;
                    this.currentProfileState = instance.resource_recommendations.cpu_min.current_profile_state.state;
                }

                break;

            case ResourceProfileId.MEMORY_MAX:
                if (instance.resource_profile == null) {
                    instance.metrics?.memory_running_averages.max;
                    break;
                }

                this.usageValue = instance.resource_profile?.memory.max_usage;
                this.usagePercentage = instance.resource_profile?.memory.max_usage_percentage;
                this.allocationValue = instance.resource_profile?.memory.max_allocatable;

                if (instance.resource_recommendations != null) {
                    this.recommendedProfile = instance.resource_recommendations.cpu_min.recommended_profile;
                    this.currentProfileState = instance.resource_recommendations.memory_max.current_profile_state.state;
                }

                break;

            case ResourceProfileId.MEMORY_MIN:
                if (instance.resource_profile == null) {
                    instance.metrics?.memory_running_averages.min;
                    break;
                }

                this.usageValue = instance.resource_profile?.memory.min_usage;
                this.usagePercentage = instance.resource_profile?.memory.min_usage_percentage;
                this.allocationValue = instance.resource_profile?.memory.min_allocatable;

                if (instance.resource_recommendations != null) {
                    this.recommendedProfile = instance.resource_recommendations.cpu_min.recommended_profile;
                    this.currentProfileState = instance.resource_recommendations.memory_min.current_profile_state.state;
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
    }

    private applyRecommendation(recommendation: ModelInstanceRecommendations, resourceProfileId: ResourceProfileId | string) {
        this.recommendedProfile = {
            id: this.resourceProfileId! as ResourceProfileId,
            state: ResourceProfileState.RECOMMENDED,
            min: 45,
            max: 55
        };

        switch (resourceProfileId) {
            case ResourceProfileId.CPU_MAX:
                this.allocationPercentage = recommendation.cpu_max.current_allocation_percentage;
                this.allocationValue = recommendation.cpu_max.current_allocation_value;
                this.recommendedValue = recommendation.cpu_max.recommended_value;
                this.currentProfileState = recommendation.cpu_max.current_allocation_profile_state.state;

                break;

            case ResourceProfileId.CPU_MIN:
                this.allocationPercentage = recommendation.cpu_min.current_allocation_percentage;
                this.allocationValue = recommendation.cpu_min.current_allocation_value;
                this.recommendedValue = recommendation.cpu_min.recommended_value;
                this.currentProfileState = recommendation.cpu_min.current_allocation_profile_state.state;

                break;

            case ResourceProfileId.MEMORY_MAX:
                this.allocationPercentage = recommendation.memory_max.current_allocation_percentage;
                this.allocationValue = recommendation.memory_max.current_allocation_value;
                this.recommendedValue = recommendation.memory_max.recommended_value;
                this.currentProfileState = recommendation.memory_max.current_allocation_profile_state.state;

                break;

            case ResourceProfileId.MEMORY_MIN:
                this.allocationPercentage = recommendation.memory_min.current_allocation_percentage;
                this.allocationValue = recommendation.memory_min.current_allocation_value;
                this.recommendedValue = recommendation.memory_min.recommended_value;
                this.currentProfileState = recommendation.memory_min.current_allocation_profile_state.state;

                break;
        }

        if (this.currentProfileState != null) {
            this.ngClass[`profile-state-${this.currentProfileState.toLowerCase()}`] = true;
            this.indicatorClass[`profile-state-${this.currentProfileState.toLowerCase()}`] = true;
        }
    }

    setFill() {
        if (this.instance != null) {
            if ((this.usagePercentage ?? 0) >= 100) {
                this.indicatorPosition = '0px';
                this.indicatorWidth = '0px';
            } else {
                let indicatorPositionValue = 150 * ((this.usagePercentage ?? 0) / 100);
                this.indicatorPosition = `${indicatorPositionValue}px`;
                this.indicatorWidth = `${150 - indicatorPositionValue}px`;
            }
        } else if (this.recommendation != null && this.allocationPercentage != null) {
            if (this.allocationPercentage <= -100) {
                this.indicatorPosition = '0px';
                this.indicatorWidth = '0px';
            } else if (this.allocationPercentage >= 100) {
                this.indicatorPosition = '150px';
                this.indicatorWidth = '0px';
            } else {
                // 0 = 150 / 2
                let indicatorPositionValue = 150 / 2;
                indicatorPositionValue = indicatorPositionValue + (indicatorPositionValue * this.allocationPercentage / 100);
                this.indicatorPosition = `${indicatorPositionValue}px`;
                this.indicatorWidth = `${150 - indicatorPositionValue}px`;
            }
        }

        if (this.recommendation != null) {
            const recommendedIndicatorPosition = 150 / 2;
            this.recommendedIndicatorPosition = `${recommendedIndicatorPosition}px`;
        }

        if (this.recommendedProfile == null) {
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
        this.fillGradient = `linear-gradient(90deg, #f79e3a ${gradientPercentages[0]}%, #f8f84a ${gradientPercentages[1]}%, #31ec5a ${gradientPercentages[2]}%, #31ec5a ${gradientPercentages[3]}%, #f8f84a ${gradientPercentages[4]}%, #f79e3a ${gradientPercentages[5]}%)`
    }
}