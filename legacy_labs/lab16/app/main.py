from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.configuration import APP_HOST, APP_PORT
from app.fraud_query_service import FraudQueryService

app = FastAPI(title="Hybrid NoSQL Fraud Query Service", version="1.0.0")
service = FraudQueryService()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "message": "Hybrid Fraud Query service is available",
        "backends": service.backend_status,
    }


@app.get("/transaction/{txn_id}")
def get_transaction(txn_id: str) -> dict:
    transaction = service.get_transaction(txn_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail=f"Transaction {txn_id} not found")
    return {"transaction": transaction, "backend_status": service.backend_status}


@app.get("/user/{user_id}")
def get_user_profile(user_id: str, limit: int = 10) -> dict:
    user_profile = service.get_user_profile(user_id, limit=limit)
    return {"user_id": user_id, "user_profile": user_profile, "backend_status": service.backend_status}


@app.get("/fraud/{user_id}")
def get_fraud(user_id: str, max_hops: int = 3) -> dict:
    result = service.get_combined_response(user_id=user_id)
    result["max_hops"] = max_hops
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=APP_HOST, port=APP_PORT, reload=False)
