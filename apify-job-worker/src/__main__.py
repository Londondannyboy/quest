"""Allow running worker with: python -m src.worker"""

from .worker import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
