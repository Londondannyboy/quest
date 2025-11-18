"""
Test Zep Graph Screenshot Locally

Standalone script to prove the screenshot feature works.
"""

import asyncio
from playwright.async_api import async_playwright
import cloudinary
import cloudinary.uploader
from pathlib import Path

# Cloudinary config
cloudinary.config(
    cloud_name="dca1swjka",
    api_key="635344679629569",
    api_secret="YOUR_CLOUDINARY_SECRET"  # You'll need to add this
)

ZEP_API_KEY = "z_1dWlkIjoiMmNkYWVjZjktYTU5Ny00ZDlkLWIyMWItNTZjOWI5OTE5MTE4In0.Ssyb_PezcGgacQFq6Slg3fyFoqs8hBhvp6WsE8rO4VK_D70CT5tqDbFOs6ZTf8rw7qYfTRhLz5YFm8RR854rHg"
ZEP_PROJECT_ID = "7d00497e-a7ef-47dd-9763-112a6bbe92f2"
GRAPH_ID = "finance-knowledge"


async def test_screenshot():
    """Test capturing a screenshot of Zep graph."""
    print("🚀 Starting Zep Graph Screenshot Test...")

    async with async_playwright() as p:
        print("📱 Launching browser...")
        browser = await p.chromium.launch(headless=False)  # headless=False so you can see it

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )

        page = await context.new_page()

        # Set auth header
        await context.set_extra_http_headers({
            "Authorization": f"Api-Key {ZEP_API_KEY}"
        })

        zep_url = f"https://app.getzep.com/projects/{ZEP_PROJECT_ID}/groups/{GRAPH_ID}"
        print(f"🌐 Navigating to: {zep_url}")

        try:
            await page.goto(zep_url, wait_until="networkidle", timeout=30000)
            print("✅ Page loaded")

            # Wait for graph to render
            print("⏳ Waiting for graph to render...")
            await asyncio.sleep(5)

            # Take screenshot
            print("📸 Capturing screenshot...")
            screenshot_path = "/tmp/zep_graph_test.png"
            await page.screenshot(path=screenshot_path, full_page=False, type="png")
            print(f"✅ Screenshot saved: {screenshot_path}")

            # Upload to Cloudinary (if you add the secret)
            # print("☁️ Uploading to Cloudinary...")
            # upload_result = cloudinary.uploader.upload(
            #     screenshot_path,
            #     folder="zep-graphs-test",
            #     public_id="test_graph",
            #     resource_type="image"
            # )
            # print(f"✅ Uploaded: {upload_result.get('secure_url')}")

            print(f"\n🎉 SUCCESS! Screenshot saved to: {screenshot_path}")
            print("Open it to see the Zep graph visualization")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_screenshot())
