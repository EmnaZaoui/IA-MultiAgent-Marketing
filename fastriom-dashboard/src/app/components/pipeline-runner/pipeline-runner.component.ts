import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PipelineStateService } from '../../services/pipeline-state.service';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-pipeline-runner',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './pipeline-runner.component.html',
  styleUrls: ['./pipeline-runner.component.scss']
})
export class PipelineRunnerComponent {
  batchSize = 100;
  errorMessage = '';

  busy$ = this.pipelineState.busy$;
  pipelineRun$ = this.pipelineState.pipelineRun$;
  campaignRun$ = this.pipelineState.campaignRun$;

  constructor(private pipelineState: PipelineStateService) {}

  runFullPipeline(): void {
    this.errorMessage = '';
    this.pipelineState.launchFullPipeline(false).subscribe({
      error: (err) => { this.errorMessage = err?.error?.error || 'Erreur lors du lancement du pipeline.'; }
    });
  }

  runCampaignOnly(): void {
    this.errorMessage = '';
    this.pipelineState.launchCampaign(this.batchSize).subscribe({
      error: (err) => { this.errorMessage = err?.error?.error || "Erreur lors du lancement de l'envoi."; }
    });
  }
}