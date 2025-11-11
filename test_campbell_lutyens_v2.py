import asyncio
import os
from datetime import datetime
from temporalio.client import Client
from worker.workflows.placement_company import PlacementCompanyWorkflow

async def test_campbell_lutyens():
    """Test Campbell Lutyens profile creation with improved FireCrawl scraping"""
    
    print("🧪 Creating Company Profile: Campbell Lutyens (v2)")
    print("=" * 60)
    print(f"Temporal Address: europe-west3.gcp.api.temporal.io:7233")
    print(f"Namespace: quickstart-quest.zivkb")
    print(f"Task Queue: quest-content-queue")
    print("=" * 60)
    
    # Connect to Temporal
    client = await Client.connect(
        target_host="europe-west3.gcp.api.temporal.io:7233",
        namespace="quickstart-quest.zivkb",
        api_key=os.getenv("TEMPORAL_PROD_API_KEY")
    )
    print("✅ Connected to Temporal\n")
    
    # Company details
    company_name = "Campbell Lutyens"
    company_url = "https://campbell-lutyens.com/"
    
    print(f"Creating profile for: {company_name}")
    print(f"Website: {company_url}\n")
    
    # Use timestamp-based workflow ID to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    workflow_id = f"campbell-lutyens-{timestamp}"
    
    print(f"🚀 Starting PlacementCompanyWorkflow (ID: {workflow_id})...\n")
    
    try:
        # Execute workflow
        result = await client.execute_workflow(
            PlacementCompanyWorkflow.run,
            args=[company_name, company_url],
            id=workflow_id,
            task_queue="quest-content-queue",
        )
        
        print("\n✅ Workflow completed successfully!")
        print("\n📊 Results:")
        print(f"Company ID: {result.get('company_id')}")
        print(f"Slug: {result.get('slug')}")
        print(f"Status: {result.get('status')}")
        print(f"Data Completeness: {result.get('data_completeness', 0):.1%}")
        
        if result.get('validation_errors'):
            print(f"\n⚠️ Validation Errors:")
            for error in result['validation_errors']:
                print(f"  - {error}")
        
        print(f"\n🌐 View profile at: https://placement.quest/companies/{result.get('slug')}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_campbell_lutyens())
