"""
FastAPI server for triggering Temporal workflows via HTTP
"""
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from temporalio.client import Client
from workflows.placement_company import PlacementCompanyWorkflow
from workflows.relocation_company import RelocationCompanyWorkflow

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Quest Workflow API")

# Temporal client (will be initialized on startup)
temporal_client = None


class CompanyRequest(BaseModel):
    company_name: str
    company_url: str


@app.on_event("startup")
async def startup():
    """Connect to Temporal on startup"""
    global temporal_client

    temporal_address = os.getenv("TEMPORAL_ADDRESS", "europe-west3.gcp.api.temporal.io:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "quickstart-quest.zivkb")
    temporal_api_key = os.getenv("TEMPORAL_PROD_API_KEY")

    logger.info(f"Connecting to Temporal at {temporal_address}")

    temporal_client = await Client.connect(
        target_host=temporal_address,
        namespace=temporal_namespace,
        api_key=temporal_api_key,
    )

    logger.info("✅ Connected to Temporal")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "quest-workflow-api"}


@app.post("/workflows/placement-company")
async def create_placement_company(request: CompanyRequest):
    """Trigger PlacementCompanyWorkflow"""
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    try:
        # Generate workflow ID from company name
        workflow_id = f"placement-{request.company_name.lower().replace(' ', '-')}-{os.urandom(4).hex()}"

        logger.info(f"Starting PlacementCompanyWorkflow: {workflow_id}")

        # Start workflow
        handle = await temporal_client.start_workflow(
            PlacementCompanyWorkflow.run,
            args=[request.company_name, request.company_url],
            id=workflow_id,
            task_queue="quest-content-queue",
        )

        logger.info(f"✅ Workflow started: {workflow_id}")

        return {
            "success": True,
            "workflow_id": workflow_id,
            "run_id": handle.id,
            "company_name": request.company_name,
            "message": "Placement company workflow started successfully"
        }

    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflows/relocation-company")
async def create_relocation_company(request: CompanyRequest):
    """Trigger RelocationCompanyWorkflow"""
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    try:
        # Generate workflow ID from company name
        workflow_id = f"relocation-{request.company_name.lower().replace(' ', '-')}-{os.urandom(4).hex()}"

        logger.info(f"Starting RelocationCompanyWorkflow: {workflow_id}")

        # Start workflow
        handle = await temporal_client.start_workflow(
            RelocationCompanyWorkflow.run,
            args=[request.company_name, request.company_url],
            id=workflow_id,
            task_queue="quest-content-queue",
        )

        logger.info(f"✅ Workflow started: {workflow_id}")

        return {
            "success": True,
            "workflow_id": workflow_id,
            "run_id": handle.id,
            "company_name": request.company_name,
            "message": "Relocation company workflow started successfully"
        }

    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
