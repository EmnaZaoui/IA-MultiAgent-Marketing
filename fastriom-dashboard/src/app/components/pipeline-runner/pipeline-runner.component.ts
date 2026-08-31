import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-pipeline-runner',
  standalone: true,
  imports: [CommonModule, FormsModule , RouterModule],
  templateUrl: './pipeline-runner.component.html',
  styleUrls: ['./pipeline-runner.component.scss']
})
export class PipelineRunnerComponent {
  loadingPipeline = false;
  loadingCampaign = false;
  batchSize = 100;

  currentRun: any = null;
  currentCampaign: any = null;
  errorMessage = '';

  private pollInterval: any = null;

  constructor(private api: ApiService) {}

  runFullPipeline(): void {
    this.errorMessage = '';
    this.loadingPipeline = true;

    this.api.runFullPipeline(false).subscribe({
      next: (data) => {
        this.currentRun = data.run;
        this.loadingPipeline = false;
        this.startPolling(data.run.id);
      },
      error: (err) => {
        this.errorMessage = err?.error?.error || 'Erreur lors du lancement du pipeline.';
        this.loadingPipeline = false;
      }
    });
  }

  runCampaignOnly(): void {
    this.errorMessage = '';
    this.loadingCampaign = true;

    this.api.sendBatch(this.batchSize).subscribe({
      next: (data) => { this.currentCampaign = data.campaign_run; this.loadingCampaign = false; },
      error: (err) => {
        this.errorMessage = err?.error?.error || "Erreur lors du lancement de l'envoi.";
        this.loadingCampaign = false;
      }
    });
  }

  private startPolling(runId: number): void {
    if (this.pollInterval) clearInterval(this.pollInterval);

    this.pollInterval = setInterval(() => {
      this.api.getPipelineRun(runId).subscribe({
        next: (data) => {
          this.currentRun = data;
          if (data.status === 'COMPLETED' || data.status === 'FAILED') {
            clearInterval(this.pollInterval);
          }
        }
      });
    }, 5000);
  }

  ngOnDestroy(): void {
    if (this.pollInterval) clearInterval(this.pollInterval);
  }
}