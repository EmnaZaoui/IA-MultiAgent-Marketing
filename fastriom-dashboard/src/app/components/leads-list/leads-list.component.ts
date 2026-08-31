import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-leads-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './leads-list.component.html',
  styleUrls: ['./leads-list.component.scss']
})
export class LeadsListComponent implements OnInit {
  leads: any[] = [];
  loading = false;
  actionInProgress: { [id: number]: string } = {};

  filterStatus = '';
  filterSector = '';
  filterSource = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void { this.loadLeads(); }

  loadLeads(): void {
    this.loading = true;
    this.api.getLeads({
      status: this.filterStatus,
      sector: this.filterSector,
      source: this.filterSource
    }).subscribe({
      next: (data) => { this.leads = data.leads || []; this.loading = false; },
      error: () => { this.loading = false; }
    });
  }

  enrich(leadId: number): void {
    this.actionInProgress[leadId] = 'enrich';
    this.api.enrichLead(leadId).subscribe({
      next: () => { this.loadLeads(); delete this.actionInProgress[leadId]; },
      error: () => { delete this.actionInProgress[leadId]; }
    });
  }

  generateEmail(leadId: number): void {
    this.actionInProgress[leadId] = 'email';
    this.api.generateEmail(leadId).subscribe({
      next: () => { this.loadLeads(); delete this.actionInProgress[leadId]; },
      error: () => { delete this.actionInProgress[leadId]; }
    });
  }

  statusBadgeClass(status: string): string {
    const map: { [key: string]: string } = {
      LEAD_IMPORTED: 'badge-neutral',
      ENRICHED: 'badge-info',
      DRAFTED: 'badge-warning',
      SENT: 'badge-success',
      FAILED: 'badge-danger'
    };
    return map[status] || 'badge-neutral';
  }
}