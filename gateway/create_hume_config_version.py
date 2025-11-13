"""
Create New Version of Hume EVI Configuration

This creates a new version of the existing config that points to
the correct gateway endpoint with Gemini + Zep
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

HUME_API_KEY = os.getenv("HUME_API_KEY")
HUME_CONFIG_ID = "54f86c53-cfc0-4adc-9af0-0c4b907cadc5"


async def create_config_version():
    """Create a new version of the Hume EVI config"""

    try:
        from hume import AsyncHumeClient

        client = AsyncHumeClient(api_key=HUME_API_KEY)

        print(f"🔄 Creating new version of config {HUME_CONFIG_ID}...")
        print(f"   New endpoint: https://quest-gateway-production.up.railway.app/voice/chat/completions\n")

        # Create new config version
        new_version = await client.empathic_voice.configs.create_config_version(
            id=HUME_CONFIG_ID,

            # Point to our new gateway endpoint with Gemini + Zep
            language_model={
                "model_provider": "CUSTOM_LANGUAGE_MODEL",
                "model_resource": "https://quest-gateway-production.up.railway.app/voice/chat/completions",
                "temperature": 0.7
            },

            # Voice settings
            voice={
                "provider": "HUME_AI",
                "name": "ITO"  # Professional, clear voice
            },

            # Event messages
            event_messages={
                "on_new_chat": {
                    "enabled": True,
                    "text": "Hi! I'm your relocation assistant. Ask me anything about moving to a new country, visas, costs, or finding the perfect place to relocate."
                }
            },

            # EVI version
            evi_version="3"
        )

        print("✅ New configuration version created successfully!\n")
        print(f"Config ID: {new_version.id}")
        print(f"Version: {new_version.version}")

        if hasattr(new_version, 'language_model') and new_version.language_model:
            lm = new_version.language_model
            if hasattr(lm, 'model_resource'):
                print(f"Endpoint: {lm.model_resource}")

        print("\n🎉 Your Hume EVI configuration is now updated:")
        print("   ✓ Gemini 2.0 Flash LLM")
        print("   ✓ Zep Knowledge Graph (relocation data)")
        print("   ✓ Gateway: quest-gateway-production.up.railway.app")
        print("\n📝 This new version will be used for all new EVI sessions!")

        return new_version

    except Exception as e:
        print(f"❌ Error creating config version: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(create_config_version())
