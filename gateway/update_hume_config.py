"""
Update Hume EVI Configuration

Updates an existing Hume EVI config to point to the correct LLM endpoint
(the one we just created with Gemini + Zep integration)
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

HUME_API_KEY = os.getenv("HUME_API_KEY")
HUME_CONFIG_ID = os.getenv("HUME_CONFIG_ID")  # The config ID you created earlier


async def list_configs():
    """List all existing Hume EVI configurations"""

    try:
        from hume import AsyncHumeClient

        client = AsyncHumeClient(api_key=HUME_API_KEY)

        print("📋 Fetching your Hume EVI configurations...\n")
        configs_response = await client.empathic_voice.configs.list_configs()

        # Handle pagination
        configs = []
        async for config in configs_response:
            configs.append(config)

        if not configs:
            print("❌ No configurations found")
            return None

        print(f"Found {len(configs)} configuration(s):\n")
        for i, config in enumerate(configs, 1):
            print(f"{i}. Name: {config.name}")
            print(f"   ID: {config.id}")
            print(f"   Version: {config.evi_version}")

            # Show current LLM endpoint if available
            if hasattr(config, 'language_model') and config.language_model:
                lm = config.language_model
                if hasattr(lm, 'model_resource'):
                    print(f"   Current endpoint: {lm.model_resource}")

            print()

        return configs

    except Exception as e:
        print(f"❌ Error listing configs: {e}")
        return None


async def update_config(config_id: str):
    """Update a Hume EVI config to use the new gateway endpoint"""

    try:
        from hume import AsyncHumeClient

        client = AsyncHumeClient(api_key=HUME_API_KEY)

        print(f"\n🔄 Updating configuration {config_id}...\n")

        # Update the configuration
        updated_config = await client.empathic_voice.configs.update_config(
            id=config_id,

            # Point to our new gateway endpoint
            language_model={
                "model_provider": "CUSTOM_LANGUAGE_MODEL",
                "model_resource": "https://quest-gateway-production.up.railway.app/voice/llm-endpoint",
                "temperature": 0.7
            },

            # Keep the existing prompt or update it
            prompt={
                "text": """You are a helpful relocation assistant for relocation.quest.

You help people with questions about:
- International relocation and corporate mobility
- Visa requirements and immigration processes
- Cost of living in different countries
- Finding the best countries for expats and digital nomads
- Corporate relocation services

Guidelines:
- Be warm, empathetic, and supportive
- Keep responses concise and conversational (voice-optimized)
- Provide specific, actionable information
- If you don't know something, admit it and suggest visiting relocation.quest for details
- Be encouraging about the relocation journey

Tone: Professional yet friendly, like a knowledgeable friend helping with a big life decision."""
            }
        )

        print("✅ Configuration updated successfully!\n")
        print(f"Config ID: {updated_config.id}")
        print(f"Name: {updated_config.name}")

        if hasattr(updated_config, 'language_model') and updated_config.language_model:
            lm = updated_config.language_model
            if hasattr(lm, 'model_resource'):
                print(f"New endpoint: {lm.model_resource}")

        print("\n📝 Your Hume EVI is now connected to:")
        print("   Gemini LLM + Zep Knowledge Graph")
        print("   via quest-gateway-production.up.railway.app")

        return updated_config

    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return None


async def main():
    """Main function"""

    print("🎙️  Hume EVI Configuration Update")
    print("=" * 50)

    if not HUME_API_KEY:
        print("❌ Error: HUME_API_KEY not found in environment")
        return

    # List existing configs
    configs = await list_configs()

    if not configs:
        print("\n❌ No configurations found to update")
        print("Run setup_hume_config.py first to create a configuration")
        return

    # Determine which config to update
    config_to_update = None

    if HUME_CONFIG_ID:
        print(f"\n✓ Using HUME_CONFIG_ID from .env: {HUME_CONFIG_ID}")
        config_to_update = HUME_CONFIG_ID
    elif len(configs) == 1:
        print(f"\n✓ Only one config found, using: {configs[0].id}")
        config_to_update = configs[0].id
    else:
        # Ask user to select
        print("\nMultiple configs found. Which one should we update?")
        choice = input(f"Enter number (1-{len(configs)}): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(configs):
                config_to_update = configs[idx].id
            else:
                print("❌ Invalid choice")
                return
        except ValueError:
            print("❌ Invalid input")
            return

    # Confirm update
    print("\n" + "=" * 50)
    print("This will update the configuration to use:")
    print("  https://quest-gateway-production.up.railway.app/voice/llm-endpoint")
    print("\nThis endpoint connects to:")
    print("  • Gemini 2.0 Flash LLM")
    print("  • Zep Knowledge Graph (your relocation data)")
    print("=" * 50)

    confirm = input("\nProceed with update? (yes/no): ").strip().lower()

    if confirm in ['yes', 'y']:
        await update_config(config_to_update)
    else:
        print("\nUpdate cancelled")


if __name__ == "__main__":
    asyncio.run(main())
