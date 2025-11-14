"""
Update Hume EVI Configuration - Create New Version with Updated Endpoint
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

HUME_API_KEY = os.getenv("HUME_API_KEY")
HUME_CONFIG_ID = "54f86c53-cfc0-4adc-9af0-0c4b907cadc5"


async def create_new_version():
    """Create a new config version with updated endpoint"""

    try:
        from hume import AsyncHumeClient

        client = AsyncHumeClient(api_key=HUME_API_KEY)

        print(f"🔄 Creating new version for config {HUME_CONFIG_ID}...")
        print(f"New endpoint: https://quest-gateway-production.up.railway.app/voice/chat/completions\n")

        # Create a new config version with the updated endpoint
        # NOTE: Hume requires SSE endpoints to end with /chat/completions
        new_version = await client.empathic_voice.configs.create_config_version(
            id=HUME_CONFIG_ID,
            evi_version="3",

            # Point to our new gateway endpoint
            # NOTE: Prompt is handled in the gateway, not in Hume config for custom models
            language_model={
                "model_provider": "CUSTOM_LANGUAGE_MODEL",
                "model_resource": "https://quest-gateway-production.up.railway.app/voice/chat/completions",
                "temperature": 0.7
            },

            # Voice settings (Hume handles voice synthesis)
            voice={
                "provider": "HUME_AI",
                "name": "ITO"
            },

            # Event messages
            event_messages={
                "on_new_chat": {
                    "enabled": True,
                    "text": "Hi! I'm your relocation assistant. I can help you with questions about moving to a new country, visa requirements, costs, and finding the perfect place to relocate. What would you like to know?"
                }
            }
        )

        print("✅ New config version created successfully!\n")
        print(f"Config ID: {HUME_CONFIG_ID}")
        print(f"Version: {new_version.version}")

        if hasattr(new_version, 'language_model') and new_version.language_model:
            lm = new_version.language_model
            if hasattr(lm, 'model_resource'):
                print(f"Endpoint: {lm.model_resource}")

        print("\n✅ Your Hume EVI is now connected to:")
        print("   • Gemini 2.0 Flash LLM")
        print("   • Zep Knowledge Graph")
        print("   • quest-gateway-production.up.railway.app")
        print("\n📝 Note: This new version is now active for this config!")

        return True

    except Exception as e:
        print(f"❌ Error creating config version: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(create_new_version())
