import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HeaderComponent } from './components/header/header.component';
import { FormsModule } from '@angular/forms';
import { PipelineStateService } from './services/pipeline-state.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent, FormsModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  title = 'fastriom-dashboard';

  constructor(private pipelineState: PipelineStateService) {}

  ngOnInit(): void {
    this.pipelineState.restoreStateOnStartup();
  }
}