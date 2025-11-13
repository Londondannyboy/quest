"""
Update Hume EVI Configuration (No prompts - just do it)
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

HUME_API_KEY = os.getenv("HUME_API_KEY")
HUME_CONFIG_ID = "54f86c53-cfc0-4adc-9af0-0c4b907cadc5"


async def update_config():
    """Update the Hume EVI config"""

    try:
        from hume import AsyncHumeClient

        client = AsyncHumeClient(api_key=HUME_API_KEY)

        print(f"🔄 Updating configuration {HUME_CONFIG_ID}...")
        print(f"   From: https://quest-worker-production.up.railway.app/api/llm/chat/completions")
        print(f"   To:   https://quest-gateway-production.up.railway.app/voice/llm-endpoint\n")

        # Update the configuration
        updated_config = await client.empathic_voice.configs.update_config(
            id=HUME_CONFIG_ID,

            # Point to our new gateway endpoint
            language_model={
                "model_provider": "CUSTOM_LANGUAGE_MODEL",
                "model_resource": "https://quest-gateway-production.up.railway.app/voice/llm-endpoint",
                "temperature": 0.7
            }
        )

        print("✅ Configuration updated successfully!\n")
        print(f"Config ID: {updated_config.id}")
        print(f"Name: {updated_config.name}")

        if hasattr(updated_config, 'language_model') and updated_config.language_model:
            lm = updated_config.language_model
            if hasattr(lm, 'model_resource'):
                print(f"New endpoint: {lm.model_resource}")

        print("\n🎉 Your Hume EVI is now connected to:")
        print("   ✓ Gemini 2.0 Flash LLM")
        print("   ✓ Zep Knowledge Graph")
        print("   ✓ via quest-gateway-production.up.railway.app")

        return updated_config

    except Exception as e:
        print(f"❌ Error updating config: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(update_config())
