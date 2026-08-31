import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // ── Leads ──────────────────────────────────────────────
  getLeads(params: { 
    status?: string; 
    sector?: string; 
    source?: string; 
    page?: number;
    per_page?: number;  // ← AJOUTER CETTE LIGNE
  } = {}): Observable<any> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') query.set(key, String(value));
    });
    return this.http.get(`${this.baseUrl}/leads?${query.toString()}`);
  }

  discoverLeads(payload: { query: string; business_type_hint?: string; max_results?: number }): Observable<any> {
    return this.http.post(`${this.baseUrl}/leads/discover`, payload);
  }

  enrichLead(leadId: number): Observable<any> {
    return this.http.post(`${this.baseUrl}/leads/${leadId}/enrich`, {});
  }

  generateEmail(leadId: number): Observable<any> {
    return this.http.post(`${this.baseUrl}/leads/${leadId}/generate-email`, {});
  }

  // ── Pipeline complet ───────────────────────────────────
  runFullPipeline(allowProductionSend: boolean = false): Observable<any> {
    return this.http.post(`${this.baseUrl}/pipeline/run`, { allow_production_send: allowProductionSend });
  }

  getPipelineRun(runId: number): Observable<any> {
    return this.http.get(`${this.baseUrl}/pipeline/run/${runId}`);
  }

  listPipelineRuns(): Observable<any> {
    return this.http.get(`${this.baseUrl}/pipeline/runs`);
  }

  // ── Campagnes d'envoi ──────────────────────────────────
  sendBatch(batchSize: number = 100): Observable<any> {
    return this.http.post(`${this.baseUrl}/campaigns/send-batch`, { batch_size: batchSize });
  }

  getCampaign(runId: number): Observable<any> {
    return this.http.get(`${this.baseUrl}/campaigns/${runId}`);
  }
}