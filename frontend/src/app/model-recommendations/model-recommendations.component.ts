import { Component, inject, OnInit, Signal, TrackByFunction } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { ErsiliaLoaderComponent } from '../ersilia-loader/ersilia-loader.component';
import { ModelInstanceResourceComponent } from '../model-instance-resource/model-instance-resource.component';
import { MatFormFieldModule } from '@angular/material/form-field';
import { FormsModule } from '@angular/forms';
import { RecommendationsService } from '../../services/recommendations.service';
import { ModelInstanceRecommendations } from '../../objects/recommendations';

@Component({
  selector: 'app-model-recommendations',
  standalone: true,
  imports: [MatButtonModule, FormsModule, MatFormFieldModule, CommonModule, MatIconModule,
    ErsiliaLoaderComponent, ModelInstanceResourceComponent],
  templateUrl: './model-recommendations.component.html',
  styleUrl: './model-recommendations.component.scss'
})
export class ModelRecommendationsComponent implements OnInit {

  private recommendationsService = inject(RecommendationsService);

  recommendations: Signal<ModelInstanceRecommendations[]>;
  loading: Signal<boolean>;

  constructor() {
    this.loading = this.recommendationsService.computeRecommendationsLoadingSignal<boolean>(
      _loading => _loading
    );

    this.recommendations = this.recommendationsService.getRecommendations();
  }

  ngOnInit(): void {
    this.load();
  }

  load() {
    if (this.loading()) {
      return;
    }

    this.recommendationsService.loadRecommendations();
  }

  trackBy: TrackByFunction<ModelInstanceRecommendations> = (index: number, item: ModelInstanceRecommendations) => {
    return `${item.model_id}_${item.last_updated}`;
  };

  apply(item: ModelInstanceRecommendations) {
    if (this.loading()) {
      return;
    }

    this.recommendationsService.applyModelRecommendations(item);
  }
}
