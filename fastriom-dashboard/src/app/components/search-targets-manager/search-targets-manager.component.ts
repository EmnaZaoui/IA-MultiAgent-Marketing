import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { RouterModule } from '@angular/router';

interface SearchTarget {
  id: string;
  query: string;
  business_type_hint: string;
}

@Component({
  selector: 'app-search-targets-manager',
  standalone: true,  
  imports: [CommonModule, FormsModule , RouterModule], 
  templateUrl: './search-targets-manager.component.html',
  styleUrls: ['./search-targets-manager.component.scss']
})
export class SearchTargetsManagerComponent implements OnInit {
  targets: SearchTarget[] = [];
  maxResultsPerTarget = 8;
  loading = false;
  errorMessage = '';
  successMessage = '';

  formMode: 'none' | 'add' | 'edit' = 'none';
  formQuery = '';
  formBusinessTypeHint = '';
  editingTargetId: string | null = null;
  targetPendingDeletion: SearchTarget | null = null;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadTargets();
  }

  loadTargets(): void {
    this.loading = true;
    this.api.getSearchTargets().subscribe({
      next: (data) => {
        this.targets = data.targets || [];
        this.maxResultsPerTarget = data.max_results_per_target || 8;
        this.loading = false;
      },
      error: () => {
        this.errorMessage = "Impossible de charger les cibles de recherche.";
        this.loading = false;
      }
    });
  }

  openAddForm(): void {
    this.formMode = 'add';
    this.formQuery = '';
    this.formBusinessTypeHint = '';
    this.editingTargetId = null;
    this.clearMessages();
  }

  openEditForm(target: SearchTarget): void {
    this.formMode = 'edit';
    this.formQuery = target.query;
    this.formBusinessTypeHint = target.business_type_hint;
    this.editingTargetId = target.id;
    this.clearMessages();
  }

  cancelForm(): void {
    this.formMode = 'none';
    this.editingTargetId = null;
  }

  submitForm(): void {
    if (!this.formQuery.trim()) {
      this.errorMessage = 'La requête de recherche est obligatoire.';
      return;
    }

    const payload = { 
      query: this.formQuery.trim(), 
      business_type_hint: this.formBusinessTypeHint.trim() 
    };

    const request$ = this.formMode === 'edit' && this.editingTargetId
      ? this.api.updateSearchTarget(this.editingTargetId, payload)
      : this.api.addSearchTarget(payload);

    request$.subscribe({
      next: () => {
        this.successMessage = this.formMode === 'edit' 
          ? 'Cible modifiée avec succès.' 
          : 'Cible ajoutée avec succès.';
        this.formMode = 'none';
        this.loadTargets();
      },
      error: (err) => {
        this.errorMessage = err?.error?.error || "Une erreur est survenue.";
      }
    });
  }

  confirmDelete(target: SearchTarget): void {
    this.targetPendingDeletion = target;
  }

  cancelDelete(): void {
    this.targetPendingDeletion = null;
  }

  executeDelete(): void {
    if (!this.targetPendingDeletion) return;

    this.api.deleteSearchTarget(this.targetPendingDeletion.id).subscribe({
      next: () => {
        this.successMessage = 'Cible supprimée avec succès.';
        this.targetPendingDeletion = null;
        this.loadTargets();
      },
      error: (err) => {
        this.errorMessage = err?.error?.error || "Impossible de supprimer cette cible.";
        this.targetPendingDeletion = null;
      }
    });
  }

  saveMaxResults(): void {
    this.api.updateMaxResultsPerTarget(this.maxResultsPerTarget).subscribe({
      next: () => { 
        this.successMessage = 'Paramètre mis à jour avec succès.'; 
      },
      error: (err) => { 
        this.errorMessage = err?.error?.error || "Impossible de mettre à jour ce paramètre."; 
      }
    });
  }

  private clearMessages(): void {
    this.errorMessage = '';
    this.successMessage = '';
  }
}