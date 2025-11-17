"""
Create First Avenue company using Temporal workflow
Tests the new Flux Kontext semi-cartoon image generation
"""

import asyncio
import sys
import os
from pathlib import Path

# Add company-worker to path
sys.path.insert(0, str(Path(__file__).parent / "company-worker"))

from temporalio.client import Client
from dotenv import load_dotenv

# Load environment
load_dotenv()
load_dotenv("company-worker/.env")


async def create_company():
    """Create First Avenue company with semi-cartoon images"""

    print('🚀 Connecting to Temporal Cloud...')

    # Connect to Temporal
    client = await Client.connect(
        os.getenv('TEMPORAL_ADDRESS'),
        namespace=os.getenv('TEMPORAL_NAMESPACE'),
        api_key=os.getenv('TEMPORAL_API_KEY'),
        tls=True
    )

    print('✅ Connected successfully\n')
    print('🏢 Creating First Avenue (https://www.firstavenue.com/)')
    print('   Category: Placement Agent')
    print('   Style: Semi-cartoon illustration (NOT photorealistic)')
    print('   Model: Flux Kontext Max for company images')
    print('   Colors: Navy blue, charcoal gray, tech blue accents\n')

    # Workflow input
    workflow_input = {
        'url': 'https://www.firstavenue.com/',
        'category': 'placement',
        'app': 'placement',
        'jurisdiction': 'US',
        'force_update': False
    }

    # Start workflow
    from src.workflows.company_creation import CompanyCreationWorkflow

    workflow_id = f'create-first-avenue-test-{int(asyncio.get_event_loop().time())}'

    handle = await client.start_workflow(
        CompanyCreationWorkflow.run,
        workflow_input,
        id=workflow_id,
        task_queue=os.getenv('TEMPORAL_TASK_QUEUE')
    )

    print(f'⏳ Workflow started: {workflow_id}')
    print(f'   View live: https://cloud.temporal.io/namespaces/{os.getenv("TEMPORAL_NAMESPACE")}/workflows/{workflow_id}\n')

    print('📊 Timeline:')
    print('   [0-60s]  Research: Serper, Crawl4AI, Firecrawl, Exa, Logo')
    print('   [60-90s] Generate Profile with Claude Sonnet 4.5')
    print('   [90-180s] 🎨 Generate Semi-Cartoon Images:')
    print('             → Featured image (Kontext Max, $0.10)')
    print('             → Hero image (Kontext Max, $0.10)')
    print('             → Upload to Cloudinary')
    print('   [180s+]  Save to database & sync to Zep\n')

    print('⏰ Waiting for completion (this may take 2-3 minutes)...\n')

    try:
        result = await handle.result()

        print('\n' + '='*70)
        print('🎉 SUCCESS! First Avenue Created')
        print('='*70 + '\n')

        print(f'📋 Status: {result["status"]}')
        print(f'🆔 Company ID: {result["company_id"]}')
        print(f'🔗 Slug: {result["slug"]}')
        print(f'🏢 Name: {result.get("name", "First Avenue")}\n')

        print('🎨 GENERATED IMAGES (Semi-Cartoon Style):')
        print('-' * 70)

        featured = result.get("featured_image_url")
        hero = result.get("hero_image_url")

        if featured:
            print(f'✅ Featured Image (1200x630):')
            print(f'   {featured}')
            print(f'   → Semi-cartoon business card design')
            print(f'   → Logo integrated into stylized scene')
            print(f'   → Navy blue, charcoal gray, tech blue palette\n')
        else:
            print('❌ Featured image not generated\n')

        if hero:
            print(f'✅ Hero Image (16:9):')
            print(f'   {hero}')
            print(f'   → Corporate office environment')
            print(f'   → Stylized cartoon professionals')
            print(f'   → Glass walls, minimalist design')
            print(f'   → Maintains consistency with featured image\n')
        else:
            print('❌ Hero image not generated\n')

        print('💰 COSTS:')
        print('-' * 70)
        total = result.get("research_cost", 0)
        print(f'   Total: ${total:.4f}')
        print(f'   Images: ~$0.20 (2 × Kontext Max @ $0.10 each)')
        print(f'   Research: ~${total - 0.20:.4f}\n')

        print('📊 QUALITY METRICS:')
        print('-' * 70)
        print(f'   Research Confidence: {result.get("research_confidence", 0):.2%}')
        print(f'   Data Completeness: {result.get("data_completeness", 0):.0f}%')
        print(f'   Related Articles: {result.get("related_articles_count", 0)}')
        print(f'   Zep Graph ID: {result.get("zep_graph_id", "N/A")}\n')

        print('🔍 NEXT STEPS:')
        print('-' * 70)
        print('1. Open image URLs above to verify semi-cartoon style')
        print('2. Check for visual consistency between featured & hero')
        print('3. Verify color palette (navy, charcoal, tech blue)')
        print('4. Confirm NOT photorealistic - should be stylized digital art')
        print('5. Check Temporal UI for workflow execution details\n')

        return result

    except Exception as e:
        print(f'\n❌ Workflow failed: {e}')
        print('\nCheck Temporal UI for details:')
        print(f'https://cloud.temporal.io/namespaces/{os.getenv("TEMPORAL_NAMESPACE")}/workflows/{workflow_id}\n')
        raise


if __name__ == "__main__":
    try:
        result = asyncio.run(create_company())
        print('✅ Script completed successfully')
        sys.exit(0)
    except KeyboardInterrupt:
        print('\n\n⚠️  Interrupted by user')
        sys.exit(1)
    except Exception as e:
        print(f'\n\n❌ Error: {e}')
        sys.exit(1)
