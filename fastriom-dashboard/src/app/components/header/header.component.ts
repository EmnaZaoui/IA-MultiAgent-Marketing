import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';  
import { environment } from '../../../environments/environment';
import { PipelineStateService } from '../../services/pipeline-state.service'; 

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterModule, CommonModule, RouterModule],  
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent {
  swaggerUrl = environment.swaggerUrl;

  busy$ = this.pipelineState.busy$;
  busyLabel$ = this.pipelineState.busyLabel$;

  constructor(private pipelineState: PipelineStateService) {}  

  openSwagger(): void {
    window.open(this.swaggerUrl, '_blank');
  }
}