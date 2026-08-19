import sys
import time
sys.path.insert(0, ".")

from app import create_app
from app.models.suppression import CampaignRun
from app.services.campaign_service import _execute_batch_send, CampaignRun as CR
from app.extensions import db

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        run = CampaignRun(status="RUNNING")
        db.session.add(run)
        db.session.commit()
        run_id = run.id

        print(f"=== Lancement du batch de production (run_id={run_id}) ===")
        print("Envoi synchrone avec délais aléatoires 2-7 min entre chaque email...")
        _execute_batch_send(app, run_id, batch_size=100)

        final_run = CampaignRun.query.get(run_id)
        print(f"\n=== RÉSULTAT ===\n{final_run.to_dict()}")