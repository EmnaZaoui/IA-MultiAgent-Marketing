import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HeaderComponent } from './components/header/header.component';
import { DashboardHomeComponent } from './components/dashboard-home/dashboard-home.component';
import { LeadSearchComponent } from './components/lead-search/lead-search.component';
import { LeadsListComponent } from './components/leads-list/leads-list.component';
import { PipelineRunnerComponent } from './components/pipeline-runner/pipeline-runner.component';
import { AboutComponent } from './components/about/about.component';

@NgModule({
  declarations: [
    AppComponent,
    HeaderComponent,
    DashboardHomeComponent,
    LeadSearchComponent,
    LeadsListComponent,
    PipelineRunnerComponent,
    AboutComponent
  ],
  imports: [BrowserModule, HttpClientModule, FormsModule, AppRoutingModule],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule {}