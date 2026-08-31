import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-dashboard-home',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard-home.component.html',
  styleUrls: ['./dashboard-home.component.scss']
})
export class DashboardHomeComponent implements OnInit {
  totalLeads = 0;
  leadsBySector: { [key: string]: number } = { };
  leadsByStatus: { [key: string]: number } = {};
  recentRuns: any[] = [];
  loading = true;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadStats();
  }

  loadStats(): void {
    this.loading = true;
    this.api.getLeads({ per_page: 1000 }).subscribe({
      next: (data) => {
        const leads = data.leads || [];
        this.totalLeads = data.total || leads.length;

        this.leadsBySector = {};
        this.leadsByStatus = {};
        for (const lead of leads) {
          this.leadsBySector[lead.sector] = (this.leadsBySector[lead.sector] || 0) + 1;
          this.leadsByStatus[lead.status] = (this.leadsByStatus[lead.status] || 0) + 1;
        }
        this.loading = false;
      },
      error: () => { this.loading = false; }
    });

    this.api.listPipelineRuns().subscribe({
      next: (data) => { this.recentRuns = (data.runs || []).slice(0, 5); },
      error: () => {}
    });
  }

  statusKeys(): string[] {
    return Object.keys(this.leadsByStatus);
  }

  sectorKeys(): string[] {
    return Object.keys(this.leadsBySector);
  }
}