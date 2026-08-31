import { Component } from '@angular/core';
import { RouterModule } from '@angular/router'; 
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-header',
  standalone: true,  
  imports: [RouterModule],  
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent {
  swaggerUrl = environment.swaggerUrl;

  openSwagger(): void {
    window.open(this.swaggerUrl, '_blank');
  }
}