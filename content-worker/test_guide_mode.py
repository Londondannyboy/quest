"""
Quick local test for guide_mode structured data output.
Generates an HTML demo file with story/guide toggle.
"""

import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

# Import the activity function directly (not as Temporal activity)
from src.activities.generation.article_generation import (
    generate_four_act_article,
    extract_structured_data
)

# Mock the activity module to avoid Temporal dependency
import src.activities.generation.article_generation as article_gen

class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARN: {msg}")
    def error(self, msg, **kwargs): print(f"ERROR: {msg}")

class MockActivity:
    logger = MockLogger()

# Patch the activity module
article_gen.activity = MockActivity()


def generate_html_demo(article: dict, guide_mode: dict, four_act: list, yolo_mode: dict = None) -> str:
    """Generate an HTML demo file with story/guide/yolo toggle."""

    title = article.get('title', 'Article')
    content = article.get('content', '')
    yolo_mode = yolo_mode or {}

    # Build checklist HTML
    checklist_html = ""
    for item in guide_mode.get('checklist', []):
        checklist_html += f'''
        <label class="flex items-start gap-3 p-3 bg-white rounded-lg border hover:border-amber-300 cursor-pointer">
            <input type="checkbox" class="mt-1 w-5 h-5 text-amber-500 rounded">
            <div>
                <div class="font-medium text-gray-900">{item.get('item', '')}</div>
                <div class="text-sm text-gray-500">{item.get('detail', '')}</div>
            </div>
        </label>'''

    # Build requirements HTML
    requirements_html = ""
    for req in guide_mode.get('requirements', []):
        requirements_html += f'''
        <div class="flex items-center gap-2">
            <svg class="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg>
            <span><strong>{req.get('requirement', '')}</strong>: {req.get('detail', '')}</span>
        </div>'''

    # Build key facts HTML
    key_facts_html = ""
    for fact in guide_mode.get('key_facts', []):
        key_facts_html += f'<li class="text-gray-700">{fact}</li>'

    # Build cost breakdown HTML
    cost_breakdown = guide_mode.get('cost_breakdown', {})
    cost_items_html = ""
    if cost_breakdown:
        for item in cost_breakdown.get('items', []):
            cost_items_html += f'''
            <div class="flex justify-between py-2 border-b">
                <span class="text-gray-600">{item.get('item', '')}</span>
                <span class="font-semibold">{item.get('amount', '')}</span>
            </div>'''

    # Build 4-act sections HTML
    sections_html = ""
    for i, section in enumerate(four_act[:4]):
        sections_html += f'''
        <section class="mb-12">
            <div class="bg-gradient-to-r from-gray-100 to-gray-50 rounded-xl p-6 mb-4">
                <span class="text-amber-600 text-sm font-semibold">Act {i+1}</span>
                <h2 class="text-2xl font-bold text-gray-900 mt-1">{section.get('title', f'Section {i+1}')}</h2>
                <p class="text-amber-700 mt-2 text-sm">{section.get('factoid', '')}</p>
            </div>
            <div class="prose prose-lg max-w-none">
                <p class="text-gray-600 italic">Visual: {section.get('four_act_visual_hint', 'No visual hint')[:150]}...</p>
            </div>
        </section>'''

    # Build YOLO secondary actions HTML
    yolo_actions_html = ""
    for action in yolo_mode.get('secondary_actions', []):
        action_type = action.get('type', 'action')
        icon = {"job": "💼", "flight": "✈️", "guide": "📋", "apply": "🚀"}.get(action_type, "⚡")
        yolo_actions_html += f'''
        <a href="#" class="flex items-center gap-3 p-4 bg-gray-800 rounded-xl hover:bg-gray-700 transition group">
            <span class="text-2xl">{icon}</span>
            <div>
                <div class="font-semibold text-white group-hover:text-amber-400 transition">{action.get('label', 'Action')}</div>
                <div class="text-sm text-gray-400">{action.get('context', '')}</div>
            </div>
        </a>'''

    # Build extracted entities HTML
    entities = yolo_mode.get('extracted_entities', {})
    entities_html = ""
    if entities.get('locations'):
        entities_html += f'<span class="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm">📍 {", ".join(entities["locations"])}</span>'
    if entities.get('companies'):
        entities_html += f'<span class="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm">🏢 {", ".join(entities["companies"])}</span>'
    if entities.get('salary_range'):
        entities_html += f'<span class="px-3 py-1 bg-green-500/20 text-green-300 rounded-full text-sm">💰 {entities["salary_range"]}</span>'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .toggle-active {{ background-color: #f59e0b; color: white; }}
        .toggle-inactive {{ background-color: #e5e7eb; color: #374151; }}
        .toggle-yolo {{ background-color: #ef4444; color: white; }}
        .mode-hidden {{ display: none; }}
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="bg-gray-900 text-white py-12">
        <div class="max-w-4xl mx-auto px-4">
            <span class="text-amber-400 text-sm font-semibold uppercase tracking-wider">Relocation Guide</span>
            <h1 class="text-4xl font-bold mt-2">{title}</h1>
            <p class="text-gray-300 mt-4 text-lg">{article.get('meta_description', '')}</p>
        </div>
    </header>

    <!-- Mode Toggle -->
    <div class="sticky top-0 bg-white border-b shadow-sm z-50">
        <div class="max-w-4xl mx-auto px-4 py-3">
            <div class="flex items-center justify-between">
                <span class="text-sm text-gray-500">View mode:</span>
                <div class="flex rounded-lg overflow-hidden border">
                    <button id="btn-story" onclick="setMode('story')" class="px-4 py-2 text-sm font-medium toggle-active transition">
                        Story
                    </button>
                    <button id="btn-guide" onclick="setMode('guide')" class="px-4 py-2 text-sm font-medium toggle-inactive transition">
                        Guide
                    </button>
                    <button id="btn-yolo" onclick="setMode('yolo')" class="px-4 py-2 text-sm font-medium toggle-inactive transition">
                        🚀 YOLO
                    </button>
                </div>
            </div>
        </div>
    </div>

    <main class="max-w-4xl mx-auto px-4 py-8">

        <!-- ==================== STORY MODE ==================== -->
        <div id="story-mode">
            <div class="prose prose-lg max-w-none mb-8">
                <p class="text-xl text-gray-600">{article.get('excerpt', '')}</p>
            </div>

            {sections_html}

            <!-- Full article content -->
            <div class="prose prose-lg max-w-none mt-8 p-6 bg-white rounded-xl shadow">
                <h3>Full Article Content</h3>
                <div class="text-sm text-gray-600 max-h-96 overflow-y-auto">
                    {content[:3000]}...
                </div>
            </div>
        </div>

        <!-- ==================== GUIDE MODE ==================== -->
        <div id="guide-mode" class="mode-hidden">

            <!-- Summary Box -->
            <div class="bg-amber-50 border-l-4 border-amber-400 p-6 rounded-r-xl mb-8">
                <h2 class="text-lg font-bold text-amber-800 mb-2">Quick Summary</h2>
                <p class="text-amber-900">{guide_mode.get('summary', 'No summary available')}</p>
            </div>

            <!-- Key Facts -->
            <div class="bg-white rounded-xl shadow p-6 mb-8">
                <h2 class="text-xl font-bold text-gray-900 mb-4">Key Facts</h2>
                <ul class="space-y-2 list-disc list-inside">
                    {key_facts_html}
                </ul>
            </div>

            <!-- Requirements Box -->
            <div class="bg-blue-50 rounded-xl p-6 mb-8">
                <h2 class="text-xl font-bold text-blue-900 mb-4">Requirements</h2>
                <div class="space-y-3">
                    {requirements_html}
                </div>
            </div>

            <!-- Checklist -->
            <div class="bg-white rounded-xl shadow p-6 mb-8">
                <h2 class="text-xl font-bold text-gray-900 mb-4">Your Checklist</h2>
                <div class="space-y-3">
                    {checklist_html}
                </div>
            </div>

            <!-- Cost Breakdown -->
            {f"""
            <div class="bg-green-50 rounded-xl p-6 mb-8">
                <h2 class="text-xl font-bold text-green-900 mb-4">Cost Breakdown</h2>
                <div class="text-2xl font-bold text-green-700 mb-4">{cost_breakdown.get('total_estimate', 'N/A')}</div>
                <div class="bg-white rounded-lg p-4">
                    {cost_items_html}
                </div>
                <p class="text-sm text-green-700 mt-4">{cost_breakdown.get('notes', '')}</p>
            </div>
            """ if cost_breakdown else ''}

        </div>

        <!-- ==================== YOLO MODE ==================== -->
        <div id="yolo-mode" class="mode-hidden">

            <!-- YOLO Header -->
            <div class="bg-gradient-to-br from-red-600 to-orange-500 rounded-2xl p-8 mb-8 text-white">
                <div class="text-sm uppercase tracking-wider text-red-200 mb-2">🚀 YOLO MODE</div>
                <h2 class="text-3xl font-bold mb-4">{yolo_mode.get('headline', 'Stop reading. Start doing.')}</h2>
                <p class="text-xl text-red-100">{yolo_mode.get('motivation', 'You have read enough. Time to act.')}</p>

                <!-- Extracted entities tags -->
                <div class="flex flex-wrap gap-2 mt-6">
                    {entities_html}
                </div>
            </div>

            <!-- Primary Action -->
            <div class="bg-gray-900 rounded-2xl p-8 mb-8">
                <div class="text-center">
                    <div class="text-6xl mb-4">🎯</div>
                    <h3 class="text-2xl font-bold text-white mb-2">{yolo_mode.get('primary_action', {}).get('label', 'Take Action') if yolo_mode.get('primary_action') else 'Take Action'}</h3>
                    <p class="text-gray-400 mb-6">{yolo_mode.get('primary_action', {}).get('description', 'The time is now.') if yolo_mode.get('primary_action') else 'The time is now.'}</p>
                    <a href="#" class="inline-block bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white font-bold text-lg px-8 py-4 rounded-xl transition transform hover:scale-105 shadow-lg">
                        Just Fucking Do It →
                    </a>
                </div>
            </div>

            <!-- Secondary Actions -->
            <div class="grid md:grid-cols-2 gap-4 mb-8">
                {yolo_actions_html}
            </div>

            <!-- Disclaimer -->
            <div class="bg-gray-100 rounded-xl p-6 text-sm text-gray-600">
                <div class="font-semibold text-gray-700 mb-2">⚠️ Real Talk</div>
                <p>YOLO Mode is motivational entertainment, not financial, legal, or career advice.
                We're not responsible if you actually book a one-way flight.
                (But honestly? You probably should. Life's short.)
                Do your own research. Then do the thing.</p>
            </div>

        </div>

        <!-- Debug: Raw JSON -->
        <details class="mt-8 bg-gray-100 rounded-xl p-4">
            <summary class="cursor-pointer font-semibold text-gray-700">Debug: Raw JSON Data</summary>
            <div class="mt-4 space-y-4">
                <div>
                    <div class="text-sm font-semibold text-gray-600 mb-1">guide_mode:</div>
                    <pre class="text-xs overflow-x-auto bg-gray-900 text-green-400 p-4 rounded-lg">{json.dumps(guide_mode, indent=2)}</pre>
                </div>
                <div>
                    <div class="text-sm font-semibold text-gray-600 mb-1">yolo_mode:</div>
                    <pre class="text-xs overflow-x-auto bg-gray-900 text-amber-400 p-4 rounded-lg">{json.dumps(yolo_mode, indent=2)}</pre>
                </div>
            </div>
        </details>

    </main>

    <script>
        function setMode(mode) {{
            const storyMode = document.getElementById('story-mode');
            const guideMode = document.getElementById('guide-mode');
            const yoloMode = document.getElementById('yolo-mode');
            const btnStory = document.getElementById('btn-story');
            const btnGuide = document.getElementById('btn-guide');
            const btnYolo = document.getElementById('btn-yolo');

            // Hide all modes
            storyMode.classList.add('mode-hidden');
            guideMode.classList.add('mode-hidden');
            yoloMode.classList.add('mode-hidden');

            // Reset all buttons
            btnStory.classList.remove('toggle-active', 'toggle-yolo');
            btnStory.classList.add('toggle-inactive');
            btnGuide.classList.remove('toggle-active', 'toggle-yolo');
            btnGuide.classList.add('toggle-inactive');
            btnYolo.classList.remove('toggle-active', 'toggle-yolo');
            btnYolo.classList.add('toggle-inactive');

            // Show selected mode
            if (mode === 'story') {{
                storyMode.classList.remove('mode-hidden');
                btnStory.classList.remove('toggle-inactive');
                btnStory.classList.add('toggle-active');
            }} else if (mode === 'guide') {{
                guideMode.classList.remove('mode-hidden');
                btnGuide.classList.remove('toggle-inactive');
                btnGuide.classList.add('toggle-active');
            }} else if (mode === 'yolo') {{
                yoloMode.classList.remove('mode-hidden');
                btnYolo.classList.remove('toggle-inactive');
                btnYolo.classList.add('toggle-yolo');
                // Fun animation
                yoloMode.style.animation = 'none';
                setTimeout(() => yoloMode.style.animation = 'fadeIn 0.3s ease-out', 10);
            }}
        }}
    </script>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-4 px-8 text-sm">
        <div class="max-w-4xl mx-auto flex justify-between">
            <span>Words: {article.get('word_count', 0)}</span>
            <span>Sections: {article.get('section_count', 0)}</span>
            <span>Guide Mode: {len(guide_mode.get('key_facts', []))} facts, {len(guide_mode.get('checklist', []))} checklist items</span>
        </div>
    </footer>
</body>
</html>'''

    return html


async def test_guide_mode():
    """Test that guide_mode is generated in article output."""

    print("\n" + "="*60)
    print("Testing Guide Mode Structured Data Output")
    print("="*60 + "\n")

    # Minimal research context (just enough to generate an article)
    research_context = {
        "curated_sources": [
            {
                "title": "Cyprus Digital Nomad Visa 2025",
                "url": "https://example.com/cyprus-visa",
                "relevance_score": 9,
                "full_content": """
                Cyprus launched its Digital Nomad Visa in 2022.
                Requirements: €3,500/month income, health insurance, clean criminal record.
                Cost: €70 application fee + €150 residence permit.
                Processing time: 6-8 weeks.
                Valid for 1 year, renewable up to 3 years total.
                Tax benefits: Non-dom status available for 17 years.
                No minimum stay requirements.
                Can bring spouse and dependents.
                """
            }
        ],
        "key_facts": [
            "Cyprus Digital Nomad Visa requires €3,500/month income",
            "Application fee is €70, residence permit €150",
            "Processing takes 6-8 weeks",
            "Valid for 1 year, renewable twice",
            "Non-dom tax status for up to 17 years",
            "Launched in 2022"
        ],
        "all_source_urls": [
            {"url": "https://example.com/cyprus-visa", "title": "Cyprus Digital Nomad Visa Guide", "authority": "high_authority"}
        ]
    }

    print("Calling generate_four_act_article...")
    print(f"Topic: Cyprus Digital Nomad Visa 2025")
    print(f"App: relocation")
    print(f"Type: guide")
    print()

    result = await generate_four_act_article(
        topic="Cyprus Digital Nomad Visa 2025: Complete Guide",
        article_type="guide",
        app="relocation",
        research_context=research_context,
        target_word_count=1200,
        custom_slug=None
    )

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60 + "\n")

    if result.get("success"):
        article = result["article"]
        guide_mode = article.get("guide_mode", {})
        four_act = article.get("four_act_content", [])
        yolo_mode = article.get("yolo_mode", {})

        print(f"✅ Article generated successfully!")
        print(f"   Title: {article.get('title', 'N/A')}")
        print(f"   Words: {article.get('word_count', 0)}")

        # Log YOLO mode
        if yolo_mode.get("headline"):
            print(f"   YOLO: {yolo_mode['headline']}")

        # Generate HTML demo
        html = generate_html_demo(article, guide_mode, four_act, yolo_mode)

        output_path = "/Users/dankeegan/quest/content-worker/test_guide_mode_demo.html"
        with open(output_path, 'w') as f:
            f.write(html)

        print(f"\n✅ HTML demo generated: {output_path}")
        print(f"\nOpen in browser: file://{output_path}")

    else:
        print(f"❌ Article generation failed!")
        print(f"   Error: {result.get('error', 'Unknown')}")

    print(f"\nCost: ${result.get('cost', 0):.4f}")
    print(f"Model: {result.get('model_used', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(test_guide_mode())
