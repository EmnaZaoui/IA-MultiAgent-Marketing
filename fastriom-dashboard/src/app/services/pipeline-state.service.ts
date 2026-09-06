import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { ApiService } from './api.service';

@Injectable({ providedIn: 'root' })
export class PipelineStateService {
  private busySubject = new BehaviorSubject<boolean>(false);
  private busyLabelSubject = new BehaviorSubject<string | null>(null);
  private pipelineRunSubject = new BehaviorSubject<any | null>(null);
  private campaignRunSubject = new BehaviorSubject<any | null>(null);

  busy$: Observable<boolean> = this.busySubject.asObservable();
  busyLabel$: Observable<string | null> = this.busyLabelSubject.asObservable();
  pipelineRun$: Observable<any | null> = this.pipelineRunSubject.asObservable();
  campaignRun$: Observable<any | null> = this.campaignRunSubject.asObservable();

  private pollHandle: any = null;

  constructor(private api: ApiService) {}

  get isBusy(): boolean {
    return this.busySubject.value;
  }

  restoreStateOnStartup(): void {
    this.api.listPipelineRuns().subscribe({
      next: (data) => {
        const runningRun = (data.runs || []).find((r: any) => r.status === 'RUNNING');
        if (runningRun) {
          this.pipelineRunSubject.next(runningRun);
          this.setBusy(true, 'Un pipeline complet est en cours d\'exécution...');
          this.pollPipeline(runningRun.id);
        }
      },
      error: () => {}
    });
  }

  launchFullPipeline(allowProductionSend: boolean = false): Observable<any> {
    const request$ = this.api.runFullPipeline(allowProductionSend);
    request$.subscribe({
      next: (data) => {
        this.pipelineRunSubject.next(data.run);
        this.setBusy(true, 'Pipeline complet en cours d\'exécution...');
        this.pollPipeline(data.run.id);
      }
    });
    return request$;
  }

  launchCampaign(batchSize: number): Observable<any> {
    const request$ = this.api.sendBatch(batchSize);
    request$.subscribe({
      next: (data) => {
        this.campaignRunSubject.next(data.campaign_run);
        this.setBusy(true, "Envoi de campagne en cours d'exécution...");
        this.pollCampaign(data.campaign_run.id);
      }
    });
    return request$;
  }

  private pollPipeline(runId: number): void {
    this.clearPoll();
    this.pollHandle = setInterval(() => {
      this.api.getPipelineRun(runId).subscribe({
        next: (data) => {
          this.pipelineRunSubject.next(data);
          if (data.status === 'COMPLETED' || data.status === 'FAILED') {
            this.release();
          }
        },
        error: () => this.release()
      });
    }, 5000);
  }

  private pollCampaign(runId: number): void {
    this.clearPoll();
    this.pollHandle = setInterval(() => {
      this.api.getCampaign(runId).subscribe({
        next: (data) => {
          this.campaignRunSubject.next(data);
          if (data.status === 'COMPLETED' || data.status === 'FAILED') {
            this.release();
          }
        },
        error: () => this.release()
      });
    }, 5000);
  }

  private setBusy(value: boolean, label: string | null): void {
    this.busySubject.next(value);
    this.busyLabelSubject.next(label);
  }

  private release(): void {
    this.clearPoll();
    this.setBusy(false, null);
  }

  private clearPoll(): void {
    if (this.pollHandle) {
      clearInterval(this.pollHandle);
      this.pollHandle = null;
    }
  }
}