import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { DashboardHomeComponent } from './components/dashboard-home/dashboard-home.component';
import { LeadSearchComponent } from './components/lead-search/lead-search.component';
import { LeadsListComponent } from './components/leads-list/leads-list.component';
import { PipelineRunnerComponent } from './components/pipeline-runner/pipeline-runner.component';
import { AboutComponent } from './components/about/about.component';

const routes: Routes = [
  { path: '', component: DashboardHomeComponent },
  { path: 'recherche', component: LeadSearchComponent },
  { path: 'leads', component: LeadsListComponent },
  { path: 'pipeline', component: PipelineRunnerComponent },
  { path: 'a-propos', component: AboutComponent },
  { path: '**', redirectTo: '' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}