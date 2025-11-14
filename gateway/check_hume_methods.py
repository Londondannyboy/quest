"""
Check available Hume SDK methods
"""

import os
from dotenv import load_dotenv

load_dotenv()

HUME_API_KEY = os.getenv("HUME_API_KEY")

try:
    from hume import AsyncHumeClient
    import asyncio

    async def check():
        client = AsyncHumeClient(api_key=HUME_API_KEY)
        configs_client = client.empathic_voice.configs

        print("Available methods on configs client:")
        methods = [m for m in dir(configs_client) if not m.startswith('_')]
        for method in methods:
            print(f"  - {method}")

    asyncio.run(check())

except Exception as e:
    print(f"Error: {e}")
