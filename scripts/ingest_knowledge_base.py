import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.vectorstore_service import ingest_documents

if __name__ == "__main__":
    summary = ingest_documents("data/knowledge_base")
    print(f"Ingestion terminée: {summary}")