import { Routes } from '@angular/router';

// Assure-toi que les chemins d'import sont corrects
import { DashboardHomeComponent } from './components/dashboard-home/dashboard-home.component';
import { LeadSearchComponent } from './components/lead-search/lead-search.component';
import { LeadsListComponent } from './components/leads-list/leads-list.component';
import { PipelineRunnerComponent } from './components/pipeline-runner/pipeline-runner.component';
import { AboutComponent } from './components/about/about.component';
import { SearchTargetsManagerComponent } from './components/search-targets-manager/search-targets-manager.component';

export const routes: Routes = [
  { path: '', component: DashboardHomeComponent },
  { path: 'recherche', component: LeadSearchComponent },
  { path: 'leads', component: LeadsListComponent },
  { path: 'pipeline', component: PipelineRunnerComponent },
  { path: 'a-propos', component: AboutComponent },
  { path: 'cibles', component: SearchTargetsManagerComponent },
  { path: '**', redirectTo: '' }
  
];