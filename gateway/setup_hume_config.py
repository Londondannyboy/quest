"""
Setup Hume EVI Configuration

Creates an EVI configuration that connects to our custom language model
(Gemini + Zep integration) for relocation assistance.
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

HUME_API_KEY = os.getenv("HUME_API_KEY")
HUME_SECRET_KEY = os.getenv("HUME_SECRET_KEY")


async def create_evi_config():
    """Create Hume EVI configuration for relocation assistant"""

    try:
        from hume import AsyncHumeClient

        client = AsyncHumeClient(api_key=HUME_API_KEY)

        # Create EVI configuration
        config = await client.empathic_voice.configs.create_config(
            name="Relocation Assistant",
            evi_version="3",

            # Voice settings - use a friendly, professional voice
            voice={
                "provider": "HUME_AI",
                "name": "ITO"  # Professional, clear voice
            },

            # Language model - using Gemini via our custom endpoint
            language_model={
                "model_provider": "CUSTOM_LANGUAGE_MODEL",
                "model_resource": "https://quest-gateway-production.up.railway.app/voice/llm-endpoint",
                "temperature": 0.7
            },

            # System prompt for the assistant
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
            },

            # Event messages
            event_messages={
                "on_new_chat": {
                    "enabled": True,
                    "text": "Hi! I'm your relocation assistant. I can help you with questions about moving to a new country, visa requirements, costs, and finding the perfect place to relocate. What would you like to know?"
                },
                "on_inactivity_timeout": {
                    "enabled": True,
                    "text": "Are you still there? Feel free to ask me anything about relocation."
                },
                "on_max_duration_timeout": {
                    "enabled": True,
                    "text": "Thanks for chatting! Visit relocation.quest anytime for more information."
                }
            },

            # Timeouts
            timeouts={
                "inactivity": {
                    "enabled": True,
                    "duration_secs": 120  # 2 minutes of inactivity
                },
                "max_duration": {
                    "enabled": True,
                    "duration_secs": 1800  # 30 minutes max session
                }
            },

            # Enable nudges for engagement
            nudges={
                "enabled": True,
                "interval_secs": 60  # Gentle nudge every 60 seconds if stuck
            }
        )

        print("✅ EVI Configuration Created Successfully!")
        print(f"\nConfiguration ID: {config.id}")
        print(f"Name: {config.name}")
        print(f"Version: {config.evi_version}")

        print("\n📝 Next Steps:")
        print(f"1. Add to your .env file:")
        print(f"   HUME_CONFIG_ID={config.id}")
        print(f"\n2. Update voice.py to use this config_id")
        print(f"\n3. Create the /voice/llm-endpoint for custom LLM integration")

        return config

    except ImportError:
        print("❌ Error: hume package not installed")
        print("Run: pip install hume")
        return None

    except Exception as e:
        print(f"❌ Error creating EVI config: {e}")
        return None


async def list_existing_configs():
    """List existing EVI configurations"""

    try:
        from hume import AsyncHumeClient

        client = AsyncHumeClient(api_key=HUME_API_KEY)

        configs = await client.empathic_voice.configs.list_configs()

        print("\n📋 Existing EVI Configurations:")
        for config in configs:
            print(f"  - {config.name} (ID: {config.id})")

        return configs

    except Exception as e:
        print(f"❌ Error listing configs: {e}")
        return []


async def main():
    """Main setup function"""

    print("🎙️  Hume EVI Configuration Setup")
    print("=" * 50)

    if not HUME_API_KEY:
        print("❌ Error: HUME_API_KEY not found in environment")
        print("Please set it in your .env file")
        return

    print(f"\n✓ API Key configured")

    # List existing configs
    await list_existing_configs()

    # Ask if user wants to create new config
    print("\n" + "=" * 50)
    create = input("\nCreate new EVI configuration? (yes/no): ").strip().lower()

    if create in ['yes', 'y']:
        await create_evi_config()
    else:
        print("\nSetup cancelled. Use existing configuration.")


if __name__ == "__main__":
    asyncio.run(main())
