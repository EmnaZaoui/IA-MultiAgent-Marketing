import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { RouterModule } from '@angular/router';
import { PipelineStateService } from '../../services/pipeline-state.service';

@Component({
  selector: 'app-lead-search',
  standalone: true,
  imports: [CommonModule, FormsModule , RouterModule],
  templateUrl: './lead-search.component.html',
  styleUrls: ['./lead-search.component.scss']
})
export class LeadSearchComponent {
  query = '';
  businessTypeHint = '';
  maxResults = 10;

  loading = false;
  result: any = null;
  errorMessage = '';
  busy$ = this.pipelineState.busy$;
  constructor(private api: ApiService, private pipelineState: PipelineStateService) {}

  search(): void {
    if (!this.query.trim()) {
      this.errorMessage = 'Veuillez saisir une requête, ex: "restaurants Maldives"';
      return;
    }

    this.loading = true;
    this.errorMessage = '';
    this.result = null;

    this.api.discoverLeads({
      query: this.query.trim(),
      business_type_hint: this.businessTypeHint.trim(),
      max_results: this.maxResults
    }).subscribe({
      next: (data) => { this.result = data; this.loading = false; },
      error: (err) => {
        this.errorMessage = err?.error?.error || 'Une erreur est survenue lors de la recherche.';
        this.loading = false;
      }
    });
  }
}