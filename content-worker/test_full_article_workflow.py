#!/usr/bin/env python3
"""
Full Article-First Workflow Test
1. Write article with 4 act-aligned sections
2. Generate video prompt from article angles
3. Generate Seedance video (12s, 480p)
4. Upload to Mux
5. Sample thumbnails at 0.5s intervals
6. Create full article HTML with smart thumbnail placement
"""

import asyncio
import os
import time
import json
import replicate
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# STEP 1: THE ARTICLE (Article-First!)
# ============================================================

ARTICLE = {
    "title": "Cyprus Digital Nomad Visa 2025: Your Complete Escape Plan from the 9-to-5",
    "slug": "cyprus-digital-nomad-visa-2025-escape-plan",
    "excerpt": "Discover how Cyprus's new digital nomad visa is helping remote workers trade grey skies for Mediterranean sunshine, with tax benefits that make the move financially compelling.",
    "sections": [
        {
            "act": 1,
            "title": "The London Grind: Why Remote Workers Are Burning Out",
            "factoid": "73% of UK remote workers report feeling trapped despite location flexibility",
            "content": """
<p class="text-lg text-gray-700 leading-relaxed mb-6">
The fluorescent lights flicker overhead as another grey London morning bleeds into afternoon. You're three cups of coffee deep, staring at the same spreadsheet you've been working on since 8 AM, while rain streaks down the office windows for the 47th consecutive day.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
Sound familiar? You're not alone. A recent survey found that <strong>73% of UK remote workers</strong> report feeling trapped despite their location flexibility. The irony is brutal: you can work from anywhere, yet you're still hunched over your laptop in the same cramped flat, paying £2,000 a month for the privilege of seasonal depression.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
The truth is, remote work promised freedom but delivered isolation. When your commute is just the walk from bedroom to kitchen table, the walls start closing in. The weather doesn't help—the UK averages just 1,500 hours of sunshine annually, compared to Cyprus's glorious 3,400 hours.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
But here's what most burned-out remote workers don't realize: there's a legal, financially smart way out. And it starts with understanding what Cyprus is offering.
</p>
""",
            "visual_description": "Dark grey London office, rain pelting windows, woman at desk looking exhausted, blue monitor glow, grey suit, dreary cityscape"
        },
        {
            "act": 2,
            "title": "The Cyprus Opportunity: Tax Benefits That Actually Make Sense",
            "factoid": "Cyprus has 3,400 hours of sunshine annually vs UK's 1,500 hours",
            "content": """
<p class="text-lg text-gray-700 leading-relaxed mb-6">
Cyprus launched its Digital Nomad Visa in 2022, and it's quietly become one of Europe's best-kept secrets for remote workers seeking both lifestyle and financial optimization.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
The headline numbers are compelling: the visa allows non-EU citizens to live and work remotely in Cyprus for <strong>up to one year, renewable for two more</strong>. But the real magic is in the tax treatment.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
Under the current scheme, digital nomads working for foreign employers or clients can benefit from Cyprus's favorable tax regime. The country offers a <strong>flat 5% tax rate on pension income</strong> and various exemptions that make it attractive for high earners. More importantly, your foreign-sourced employment income may qualify for significant tax advantages if structured correctly.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
The income requirement is reasonable: you'll need to demonstrate at least <strong>€3,500 per month</strong> in income from remote work. That's approximately £3,000—achievable for most senior developers, consultants, and digital professionals.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
Compare this to paying 40% income tax in the UK while battling seasonal affective disorder, and the math becomes obvious.
</p>
""",
            "visual_description": "Woman at home looking hopeful at laptop, warm evening light, screen showing Mediterranean coastline, expression of discovery and possibility"
        },
        {
            "act": 3,
            "title": "Making the Move: From Application to Arrival",
            "factoid": "Average processing time: 4-6 weeks • Application fee: ~€70",
            "content": """
<p class="text-lg text-gray-700 leading-relaxed mb-6">
The application process is refreshingly straightforward by European bureaucracy standards. Here's what you'll need:
</p>

<ul class="list-disc list-inside space-y-2 mb-6 text-gray-700">
    <li><strong>Valid passport</strong> with at least 18 months remaining</li>
    <li><strong>Proof of remote employment</strong> or freelance contracts with non-Cyprus entities</li>
    <li><strong>Income verification</strong> showing €3,500+ monthly (bank statements, contracts)</li>
    <li><strong>Health insurance</strong> valid in Cyprus</li>
    <li><strong>Clean criminal record</strong> certificate</li>
    <li><strong>Accommodation proof</strong> (rental agreement or hotel booking)</li>
</ul>

<p class="text-gray-700 leading-relaxed mb-6">
Processing typically takes <strong>4-6 weeks</strong>. Many applicants report approval within a month. The fee is approximately €70—a fraction of what other countries charge.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
Once approved, the transition is smoother than you'd expect. Larnaca and Paphos airports have direct flights from most European capitals. The cost of living is <strong>30-40% lower than London</strong>—a two-bedroom apartment in Limassol runs about €800-1,200 monthly, compared to £1,800+ for similar in Zone 2.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
The hardest part? Telling your landlord you're not renewing the lease.
</p>
""",
            "visual_description": "Travel montage: suitcase being packed, passport, airplane window with Mediterranean view, Cyprus coastline from above, golden sunlight"
        },
        {
            "act": 4,
            "title": "Life After the Move: What Six Months in Cyprus Actually Looks Like",
            "factoid": "Most digital nomads save €1,000-2,000 more per month than in the UK",
            "content": """
<p class="text-lg text-gray-700 leading-relaxed mb-6">
Fast forward six months. It's 7 PM and you're closing your laptop on a terrace overlooking the Mediterranean. The sun is setting in that particular shade of orange that only exists in places where the sky actually remembers what blue looks like.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
Your productivity hasn't dropped—if anything, it's increased. The vitamin D helps. So does the fact that you're no longer spending mental energy fighting the weather. Your calendar still has meetings, but now they end in time for a sunset swim.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
The expat community in Cyprus is thriving. Limassol alone has become a hub for tech workers and digital nomads. Coworking spaces like Regus and WeWork have opened locations, and the informal network of remote workers means you're never short of people who understand the lifestyle.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
The best part? You're saving money while living better. Between lower rent, reduced taxes (properly structured), and the simple economics of a lower cost of living, most digital nomads report <strong>saving €1,000-2,000 more per month</strong> than they did in the UK.
</p>

<p class="text-gray-700 leading-relaxed mb-6">
That's not just a lifestyle upgrade—it's a financial one. And unlike the grey London mornings, it's sustainable.
</p>
""",
            "visual_description": "Golden sunset terrace, woman in linen dress with wine glass, friends laughing at outdoor table, Mediterranean view, warm golden light, genuine happiness"
        }
    ],
    "faq": [
        {"q": "Can I bring my family on the Cyprus Digital Nomad Visa?", "a": "Yes, the visa allows for family reunification. Your spouse and dependent children can join you under the same visa scheme."},
        {"q": "Do I need to pay Cyprus taxes on my foreign income?", "a": "Tax treatment depends on your specific situation. Generally, if you maintain tax residency elsewhere and work for a foreign employer, you may have favorable treatment. Consult a tax professional."},
        {"q": "What's the internet speed like in Cyprus?", "a": "Excellent. Major cities have fiber connections up to 1Gbps. Mobile 4G/5G coverage is comprehensive. Most cafes and coworking spaces offer reliable high-speed wifi."},
        {"q": "Can I travel within the EU on this visa?", "a": "Cyprus is an EU member, but the Digital Nomad Visa doesn't automatically grant Schengen access. You can visit Schengen countries under normal tourist rules (90 days in 180)."},
    ],
    "comparison": {
        "title": "Cyprus vs Other Digital Nomad Visas",
        "items": [
            {"country": "Cyprus", "income_req": "€3,500/mo", "tax": "Favorable", "duration": "1 year + 2 renewals", "processing": "4-6 weeks"},
            {"country": "Portugal", "income_req": "€3,040/mo", "tax": "NHR regime", "duration": "2 years", "processing": "2-3 months"},
            {"country": "Spain", "income_req": "€2,520/mo", "tax": "Beckham Law", "duration": "1 year", "processing": "1-3 months"},
            {"country": "Greece", "income_req": "€3,500/mo", "tax": "50% reduction", "duration": "1 year", "processing": "1-2 months"},
        ]
    }
}

# ============================================================
# STEP 2: GENERATE VIDEO PROMPT FROM ARTICLE
# ============================================================

def generate_video_prompt_from_article(article):
    """Extract act angles from article sections and build video prompt."""

    sections = article["sections"]

    prompt = """CRITICAL: This video must contain ABSOLUTELY NO TEXT, NO WORDS, NO LETTERS, NO NUMBERS, NO WRITING, NO SIGNS anywhere. All screens show only abstract colors, never text.

Cinematic 4-act transformation story of a remote worker escaping London for Cyprus.

"""

    for section in sections:
        act = section["act"]
        title = section["title"]
        visual = section["visual_description"]

        start = (act - 1) * 3
        end = act * 3

        prompt += f"""ACT {act} ({start}-{end} seconds): {title.upper().split(':')[0] if ':' in title else title.upper()}
{visual}. No text visible anywhere.

"""

    prompt += """Technical: Smooth cinematic transitions. High contrast between London grey (Act 1) and Cyprus golden warmth (Acts 3-4). Natural motion, emotional storytelling through visuals only.

REMINDER: ZERO TEXT IN ANY FRAME. No words, letters, or writing of any kind."""

    return prompt


# ============================================================
# STEP 3: VIDEO GENERATION
# ============================================================

async def generate_video(prompt):
    """Generate 12-second 480p video with Seedance."""

    print("=" * 70)
    print("  GENERATING VIDEO FROM ARTICLE ANGLES")
    print("=" * 70)

    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("ERROR: REPLICATE_API_TOKEN not set")
        return None

    print(f"\nPrompt length: {len(prompt)} chars")
    print("Model: bytedance/seedance-1-pro-fast")
    print("Duration: 12s | Resolution: 480p")
    print("\nGenerating... (typically 50-60 seconds)")

    client = replicate.Client(api_token=replicate_token)

    try:
        start = time.time()

        output = client.run(
            "bytedance/seedance-1-pro-fast",
            input={
                "prompt": prompt,
                "duration": 12,
                "resolution": "480p",
                "aspect_ratio": "16:9",
            }
        )

        elapsed = time.time() - start

        video_url = str(output) if not hasattr(output, 'url') else output.url

        print(f"\n✅ Video generated in {elapsed:.1f}s")
        print(f"URL: {video_url[:60]}...")

        return {"video_url": video_url, "generation_time": elapsed, "cost": 0.18}

    except Exception as e:
        print(f"ERROR: {e}")
        return None


# ============================================================
# STEP 4: MUX UPLOAD
# ============================================================

async def upload_to_mux(video_url):
    """Upload video to Mux."""

    print("\n" + "=" * 70)
    print("  UPLOADING TO MUX")
    print("=" * 70)

    mux_token_id = os.environ.get("MUX_TOKEN_ID")
    mux_token_secret = os.environ.get("MUX_TOKEN_SECRET")

    if not mux_token_id or not mux_token_secret:
        print("WARNING: MUX credentials not set")
        return None

    import mux_python

    config = mux_python.Configuration()
    config.username = mux_token_id
    config.password = mux_token_secret

    assets_api = mux_python.AssetsApi(mux_python.ApiClient(config))

    create_request = mux_python.CreateAssetRequest(
        input=[mux_python.InputSettings(url=video_url)],
        playback_policy=[mux_python.PlaybackPolicy.PUBLIC]
    )

    asset = assets_api.create_asset(create_request).data
    print(f"Asset ID: {asset.id}")

    # Wait for ready
    elapsed = 0
    while elapsed < 120:
        asset_data = assets_api.get_asset(asset.id).data
        print(f"  Status: {asset_data.status} ({elapsed}s)")
        if asset_data.status == "ready":
            break
        time.sleep(5)
        elapsed += 5

    playback_id = asset_data.playback_ids[0].id
    print(f"\n✅ Playback ID: {playback_id}")

    return {"playback_id": playback_id, "asset_id": asset.id}


# ============================================================
# STEP 5: GENERATE FULL ARTICLE HTML
# ============================================================

def generate_full_article_html(article, playback_id, video_result):
    """Generate the complete article HTML with video, thumbnails, effects."""

    base_img = f"https://image.mux.com/{playback_id}"
    stream_url = f"https://stream.mux.com/{playback_id}.m3u8"

    # Smart thumbnail selection - spread across the 12 seconds
    # Picking visually likely distinct times based on act transitions
    thumbnails = {
        "hero": f"{base_img}/thumbnail.jpg?time=10.5&width=1200&height=630&fit_mode=smartcrop",
        "section_1": f"{base_img}/thumbnail.jpg?time=1.5&width=800",  # Act 1 - London
        "section_2": f"{base_img}/thumbnail.jpg?time=4.5&width=800",  # Act 2 - Hope
        "section_3": f"{base_img}/thumbnail.jpg?time=7.0&width=800",  # Act 3 - Travel
        "section_4": f"{base_img}/thumbnail.jpg?time=10.5&width=800", # Act 4 - Cyprus
        # Additional thumbnails for callouts, FAQ - pick from different moments
        "callout_1": f"{base_img}/thumbnail.jpg?time=2.5&width=600",
        "callout_2": f"{base_img}/thumbnail.jpg?time=8.5&width=600",
        "faq_1": f"{base_img}/thumbnail.jpg?time=1.0&width=400",   # Act 1 - distinct
        "faq_2": f"{base_img}/thumbnail.jpg?time=4.0&width=400",   # Act 2 - distinct
        "faq_3": f"{base_img}/thumbnail.jpg?time=7.0&width=400",   # Act 3 - distinct
        "faq_4": f"{base_img}/thumbnail.jpg?time=10.0&width=400",  # Act 4 - distinct
        "comparison": f"{base_img}/thumbnail.jpg?time=6.0&width=800",
        "bg_translucent": f"{base_img}/thumbnail.jpg?time=10.0&width=1600",  # For background
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article['title']}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <link rel="stylesheet" href="https://unpkg.com/@mux/mux-player/dist/mux-player.css">
    <script src="https://unpkg.com/@mux/mux-player"></script>
    <style>
        .thumbnail-overlay {{
            position: relative;
            overflow: hidden;
        }}
        .thumbnail-overlay img {{
            transition: transform 0.3s ease, filter 0.3s ease;
        }}
        .thumbnail-overlay:hover img {{
            transform: scale(1.02);
        }}
        .thumbnail-gradient {{
            background: linear-gradient(to top, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.3) 40%, transparent 100%);
        }}
        .thumbnail-vignette {{
            box-shadow: inset 0 0 100px rgba(0,0,0,0.3);
        }}
        .thumbnail-warm {{
            filter: saturate(1.1) brightness(1.05);
        }}
        .thumbnail-cool {{
            filter: saturate(0.9) brightness(0.95) contrast(1.05);
        }}
        .brand-badge {{
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(4px);
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}
        .factoid {{
            background: linear-gradient(90deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%);
            border-left: 3px solid #f59e0b;
            padding: 8px 16px;
            margin-top: -4px;
            font-size: 14px;
            color: #92400e;
            font-weight: 500;
        }}
        .bg-translucent {{
            position: relative;
            overflow: hidden;
        }}
        .bg-translucent::before {{
            content: '';
            position: absolute;
            inset: 0;
            background-size: cover;
            background-position: center;
            opacity: 0.12;
            filter: blur(2px);
        }}
        .chapter-marker {{
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .chapter-marker:hover {{
            transform: scale(1.1);
        }}
        .chapter-marker.active {{
            ring: 2px;
            ring-color: #f59e0b;
        }}
    </style>
</head>
<body class="bg-white">
    <!-- Hero Section with Video -->
    <header class="relative bg-gray-900">
        <div class="max-w-6xl mx-auto">
            <mux-player
                playback-id="{playback_id}"
                accent-color="#f59e0b"
                autoplay="muted"
                loop
                class="w-full aspect-video"
            ></mux-player>
        </div>
        <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-8">
            <div class="max-w-4xl mx-auto">
                <span class="text-amber-400 text-sm font-semibold uppercase tracking-wider">Relocation Guide</span>
                <h1 class="text-4xl md:text-5xl font-bold text-white mt-2 mb-4">{article['title']}</h1>
                <p class="text-xl text-gray-200">{article['excerpt']}</p>
            </div>
        </div>
    </header>

    <!-- Chapter Timeline -->
    <div class="bg-gray-900 py-4">
        <div class="max-w-4xl mx-auto px-4">
            <div class="flex items-center gap-2">
                <span class="text-gray-500 text-xs uppercase tracking-wider mr-2">Chapters</span>
                <div class="flex-1 flex items-center gap-1">
                    <button onclick="seekTo(0)" class="chapter-marker flex-1 group">
                        <div class="h-1 bg-blue-500/60 rounded-full group-hover:bg-blue-400"></div>
                        <span class="text-xs text-gray-400 mt-1 block truncate">The Grind</span>
                    </button>
                    <button onclick="seekTo(3)" class="chapter-marker flex-1 group">
                        <div class="h-1 bg-purple-500/60 rounded-full group-hover:bg-purple-400"></div>
                        <span class="text-xs text-gray-400 mt-1 block truncate">The Dream</span>
                    </button>
                    <button onclick="seekTo(6)" class="chapter-marker flex-1 group">
                        <div class="h-1 bg-amber-500/60 rounded-full group-hover:bg-amber-400"></div>
                        <span class="text-xs text-gray-400 mt-1 block truncate">The Journey</span>
                    </button>
                    <button onclick="seekTo(9)" class="chapter-marker flex-1 group">
                        <div class="h-1 bg-emerald-500/60 rounded-full group-hover:bg-emerald-400"></div>
                        <span class="text-xs text-gray-400 mt-1 block truncate">The Reality</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
    <script>
        function seekTo(time) {{
            const player = document.querySelector('mux-player');
            if (player) player.currentTime = time;
        }}
    </script>

    <main class="max-w-4xl mx-auto px-4 py-12">
        <!-- Preamble -->
        <div class="prose prose-lg max-w-none mb-12">
            <p class="text-xl text-gray-600 leading-relaxed">
                What if you could keep your remote job, cut your taxes, and wake up to Mediterranean sunshine instead of British drizzle?
                The Cyprus Digital Nomad Visa makes it possible—and thousands of UK remote workers are already making the move.
            </p>
        </div>
"""

    # Add each section with thumbnail header
    effects = ["thumbnail-cool", "thumbnail-warm", "thumbnail-warm", "thumbnail-warm"]

    for i, section in enumerate(article["sections"]):
        thumb_key = f"section_{i+1}"
        effect = effects[i]

        factoid = section.get('factoid', '')
        act_num = section['act']
        act_start = (act_num - 1) * 3
        act_end = act_num * 3
        section_id = f"section-video-{i}"

        html += f"""
        <!-- Section {i+1}: {section['title']} -->
        <section class="mb-16">
            <!-- Section Header with Video Loop -->
            <div class="thumbnail-overlay rounded-xl mb-6 {effect}">
                <video
                    id="{section_id}"
                    class="w-full aspect-[21/9] object-cover rounded-xl"
                    muted
                    playsinline
                    loop
                    poster="{thumbnails[thumb_key]}"
                ></video>
                <div class="absolute inset-0 thumbnail-gradient rounded-xl pointer-events-none"></div>
                <!-- Branding badge - top right, out of the way -->
                <div class="absolute top-3 right-3">
                    <span class="brand-badge text-white/80">Relocation Quest</span>
                </div>
                <!-- Section title + factoid - bottom left -->
                <div class="absolute bottom-4 left-4 right-4">
                    <h2 class="text-xl md:text-2xl font-bold text-white drop-shadow-lg">{section['title']}</h2>
                    {"<p class='text-white/80 text-sm mt-1 drop-shadow'>" + factoid + "</p>" if factoid else ""}
                </div>
            </div>
            <script>
                (function() {{
                    const video = document.getElementById('{section_id}');
                    const hls = new Hls();
                    hls.loadSource('{stream_url}');
                    hls.attachMedia(video);
                    hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                        video.currentTime = {act_start};
                        video.play().catch(() => {{}});
                    }});
                    video.addEventListener('timeupdate', function() {{
                        if (video.currentTime >= {act_end}) video.currentTime = {act_start};
                    }});
                    // Intersection observer to play/pause on visibility
                    const observer = new IntersectionObserver((entries) => {{
                        entries.forEach(entry => {{
                            if (entry.isIntersecting) {{
                                video.play().catch(() => {{}});
                            }} else {{
                                video.pause();
                            }}
                        }});
                    }}, {{ threshold: 0.3 }});
                    observer.observe(video);
                }})();
            </script>

            <!-- Section Content -->
            <div class="prose prose-lg max-w-none">
                {section['content']}
            </div>
"""

        # Add callout after section 2
        if i == 1:
            html += f"""
            <!-- Callout Box -->
            <div class="my-8 bg-amber-50 border-l-4 border-amber-400 rounded-r-xl overflow-hidden">
                <div class="flex flex-col md:flex-row">
                    <div class="md:w-1/3">
                        <img src="{thumbnails['callout_1']}" alt="Cyprus lifestyle" class="w-full h-48 md:h-full object-cover" />
                    </div>
                    <div class="p-6 md:w-2/3">
                        <h3 class="text-lg font-bold text-amber-800 mb-2">💡 Pro Tip: The Tax Advantage</h3>
                        <p class="text-amber-900">
                            Cyprus operates a non-domicile tax regime. If structured correctly, your foreign-sourced income
                            may benefit from significant tax advantages compared to UK rates. Always consult a qualified
                            international tax advisor before making the move.
                        </p>
                    </div>
                </div>
            </div>
"""

        html += """
        </section>
"""

    # Comparison Table with thumbnail
    html += f"""
        <!-- Comparison Section -->
        <section class="mb-16">
            <div class="thumbnail-overlay rounded-xl mb-6 thumbnail-warm">
                <img src="{thumbnails['comparison']}" alt="Compare digital nomad visas" class="w-full aspect-[21/9] object-cover rounded-xl" />
                <div class="absolute inset-0 thumbnail-gradient rounded-xl"></div>
                <div class="absolute bottom-4 left-6">
                    <h2 class="text-2xl md:text-3xl font-bold text-white drop-shadow-lg">{article['comparison']['title']}</h2>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-gray-100">
                            <th class="p-4 font-semibold">Country</th>
                            <th class="p-4 font-semibold">Income Requirement</th>
                            <th class="p-4 font-semibold">Tax Benefits</th>
                            <th class="p-4 font-semibold">Duration</th>
                            <th class="p-4 font-semibold">Processing</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for item in article['comparison']['items']:
        highlight = 'bg-amber-50 font-semibold' if item['country'] == 'Cyprus' else ''
        html += f"""
                        <tr class="border-b {highlight}">
                            <td class="p-4">{item['country']}</td>
                            <td class="p-4">{item['income_req']}</td>
                            <td class="p-4">{item['tax']}</td>
                            <td class="p-4">{item['duration']}</td>
                            <td class="p-4">{item['processing']}</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </div>
        </section>
"""

    # FAQ Section with thumbnails
    html += f"""
        <!-- Event Timeline -->
        <section class="mb-16">
            <h2 class="text-2xl font-bold text-gray-900 mb-2">Cyprus Digital Nomad Visa Timeline</h2>
            <p class="text-gray-500 mb-8">Key dates in the program's development</p>

            <div class="relative">
                <!-- Center line -->
                <div class="absolute left-1/2 transform -translate-x-px h-full w-0.5 bg-gray-200"></div>

                <!-- Timeline events -->
                <div class="space-y-8">
                    <!-- Event 1 - Left -->
                    <div class="flex items-center">
                        <div class="w-1/2 pr-8 text-right">
                            <div class="inline-block">
                                <img src="{thumbnails['section_1']}" alt="" class="w-32 h-20 object-cover rounded-lg mb-2 ml-auto" />
                                <span class="text-amber-600 font-semibold">January 2022</span>
                                <h4 class="font-bold text-gray-900">Program Launched</h4>
                                <p class="text-sm text-gray-600">Cyprus introduces Digital Nomad Visa scheme for non-EU remote workers</p>
                            </div>
                        </div>
                        <div class="w-4 h-4 bg-amber-500 rounded-full border-4 border-white shadow z-10"></div>
                        <div class="w-1/2 pl-8"></div>
                    </div>

                    <!-- Event 2 - Right -->
                    <div class="flex items-center">
                        <div class="w-1/2 pr-8"></div>
                        <div class="w-4 h-4 bg-amber-500 rounded-full border-4 border-white shadow z-10"></div>
                        <div class="w-1/2 pl-8">
                            <div class="inline-block">
                                <img src="{thumbnails['section_2']}" alt="" class="w-32 h-20 object-cover rounded-lg mb-2" />
                                <span class="text-amber-600 font-semibold">June 2022</span>
                                <h4 class="font-bold text-gray-900">Income Threshold Set</h4>
                                <p class="text-sm text-gray-600">€3,500 monthly income requirement established</p>
                            </div>
                        </div>
                    </div>

                    <!-- Event 3 - Left -->
                    <div class="flex items-center">
                        <div class="w-1/2 pr-8 text-right">
                            <div class="inline-block">
                                <img src="{thumbnails['section_3']}" alt="" class="w-32 h-20 object-cover rounded-lg mb-2 ml-auto" />
                                <span class="text-amber-600 font-semibold">March 2023</span>
                                <h4 class="font-bold text-gray-900">First Renewals</h4>
                                <p class="text-sm text-gray-600">Initial visa holders begin renewing for additional 2-year terms</p>
                            </div>
                        </div>
                        <div class="w-4 h-4 bg-amber-500 rounded-full border-4 border-white shadow z-10"></div>
                        <div class="w-1/2 pl-8"></div>
                    </div>

                    <!-- Event 4 - Right -->
                    <div class="flex items-center">
                        <div class="w-1/2 pr-8"></div>
                        <div class="w-4 h-4 bg-emerald-500 rounded-full border-4 border-white shadow z-10"></div>
                        <div class="w-1/2 pl-8">
                            <div class="inline-block">
                                <img src="{thumbnails['section_4']}" alt="" class="w-32 h-20 object-cover rounded-lg mb-2" />
                                <span class="text-emerald-600 font-semibold">2025</span>
                                <h4 class="font-bold text-gray-900">Program Matures</h4>
                                <p class="text-sm text-gray-600">Established expat community, streamlined processing</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Highlight Section with Translucent Background -->
        <section class="mb-16 -mx-4 md:-mx-8 lg:-mx-16">
            <div class="relative py-16 px-8 overflow-hidden">
                <!-- Translucent background image -->
                <div class="absolute inset-0">
                    <img src="{thumbnails['bg_translucent']}" alt="" class="w-full h-full object-cover opacity-20" />
                    <div class="absolute inset-0 bg-gradient-to-r from-amber-50 via-white/80 to-amber-50"></div>
                </div>
                <!-- Content -->
                <div class="relative max-w-3xl mx-auto text-center">
                    <span class="text-amber-600 text-sm font-semibold uppercase tracking-wider">The Bottom Line</span>
                    <p class="text-3xl md:text-4xl font-bold text-gray-900 mt-4 mb-6">
                        Save <span class="text-amber-600">€12,000-24,000</span> per year while upgrading your lifestyle
                    </p>
                    <p class="text-gray-600 text-lg">
                        Between tax optimization, lower cost of living, and reduced commuting stress,
                        the Cyprus Digital Nomad Visa isn't just a lifestyle change—it's a financial strategy.
                    </p>
                    <div class="flex justify-center gap-8 mt-8">
                        <div class="text-center">
                            <div class="text-3xl font-bold text-gray-900">3,400</div>
                            <div class="text-sm text-gray-500">Hours of sunshine/year</div>
                        </div>
                        <div class="text-center">
                            <div class="text-3xl font-bold text-gray-900">30-40%</div>
                            <div class="text-sm text-gray-500">Lower cost of living</div>
                        </div>
                        <div class="text-center">
                            <div class="text-3xl font-bold text-gray-900">4-6</div>
                            <div class="text-sm text-gray-500">Weeks to approval</div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- FAQ Section -->
        <section class="mb-16">
            <h2 class="text-3xl font-bold text-gray-900 mb-8">Frequently Asked Questions</h2>

            <div class="grid md:grid-cols-2 gap-6">
"""

    faq_thumbs = ['faq_1', 'faq_2', 'faq_3', 'faq_4']  # All unique timestamps

    for i, faq in enumerate(article['faq']):
        thumb = thumbnails[faq_thumbs[i % len(faq_thumbs)]]
        html += f"""
                <div class="bg-gray-50 rounded-xl overflow-hidden">
                    <img src="{thumb}" alt="" class="w-full h-32 object-cover opacity-60" />
                    <div class="p-6 -mt-8 relative">
                        <div class="bg-white rounded-lg shadow-lg p-4">
                            <h3 class="font-bold text-gray-900 mb-2">{faq['q']}</h3>
                            <p class="text-gray-600 text-sm">{faq['a']}</p>
                        </div>
                    </div>
                </div>
"""

    html += """
            </div>
        </section>
"""

    # Video callout near end
    html += f"""
        <!-- Video Callout Section -->
        <section class="mb-16">
            <div class="bg-gray-900 rounded-2xl overflow-hidden">
                <div class="grid md:grid-cols-2">
                    <div class="relative">
                        <video id="callout-video" class="w-full h-full object-cover" muted playsinline></video>
                        <div class="absolute inset-0 bg-gradient-to-r from-transparent to-gray-900/50"></div>
                    </div>
                    <div class="p-8 flex flex-col justify-center">
                        <h3 class="text-2xl font-bold text-white mb-4">Ready to Make the Move?</h3>
                        <p class="text-gray-300 mb-6">
                            Join thousands of remote workers who've already discovered the Cyprus lifestyle.
                            Better weather, lower costs, and a community that understands the digital nomad life.
                        </p>
                        <a href="#" class="inline-block bg-amber-500 hover:bg-amber-600 text-white font-semibold px-6 py-3 rounded-lg transition">
                            Start Your Application →
                        </a>
                    </div>
                </div>
            </div>
            <script>
                (function() {{
                    const video = document.getElementById('callout-video');
                    const hls = new Hls();
                    hls.loadSource('{stream_url}');
                    hls.attachMedia(video);
                    hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                        video.currentTime = 9;
                        video.play();
                    }});
                    video.addEventListener('timeupdate', function() {{
                        if (video.currentTime >= 12) video.currentTime = 9;
                    }});
                }})();
            </script>
        </section>
"""

    # Footer with translucent background
    html += f"""
        <!-- Sources with Translucent Background -->
        <section class="relative rounded-xl overflow-hidden mb-12">
            <!-- Translucent background -->
            <div class="absolute inset-0">
                <img src="{thumbnails['section_4']}" alt="" class="w-full h-full object-cover opacity-10" />
                <div class="absolute inset-0 bg-gradient-to-br from-gray-50 via-white/90 to-gray-50"></div>
            </div>
            <!-- Content -->
            <div class="relative p-8">
                <h3 class="font-semibold text-gray-900 mb-4">Sources & References</h3>
                <div class="grid md:grid-cols-3 gap-4">
                    <a href="#" class="flex items-center gap-3 p-3 bg-white/60 rounded-lg hover:bg-white transition">
                        <img src="{thumbnails['faq_1']}" alt="" class="w-12 h-12 object-cover rounded" />
                        <div>
                            <p class="text-sm font-medium text-gray-900">Cyprus Ministry of Interior</p>
                            <p class="text-xs text-gray-500">Digital Nomad Visa Program</p>
                        </div>
                    </a>
                    <a href="#" class="flex items-center gap-3 p-3 bg-white/60 rounded-lg hover:bg-white transition">
                        <img src="{thumbnails['faq_2']}" alt="" class="w-12 h-12 object-cover rounded" />
                        <div>
                            <p class="text-sm font-medium text-gray-900">Nomad Capitalist</p>
                            <p class="text-xs text-gray-500">Cyprus Tax Guide 2025</p>
                        </div>
                    </a>
                    <a href="#" class="flex items-center gap-3 p-3 bg-white/60 rounded-lg hover:bg-white transition">
                        <img src="{thumbnails['faq_3']}" alt="" class="w-12 h-12 object-cover rounded" />
                        <div>
                            <p class="text-sm font-medium text-gray-900">GetGoldenVisa</p>
                            <p class="text-xs text-gray-500">European DN Visa Comparison</p>
                        </div>
                    </a>
                </div>
            </div>
        </section>

        <!-- Article Footer -->
        <footer class="pt-8 border-t">
            <div class="flex items-center gap-4">
                <img src="{thumbnails['section_4']}" alt="" class="w-16 h-16 object-cover rounded-full border-2 border-amber-200" />
                <div>
                    <p class="text-sm font-medium text-gray-900">Relocation Quest Editorial Team</p>
                    <p class="text-xs text-gray-500">
                        This article was created as a demonstration of the Article-First Video Workflow.
                        Always verify visa requirements directly with official government sources.
                    </p>
                </div>
            </div>
        </footer>
    </main>

    <!-- Generation Stats (for testing) -->
    <div class="bg-gray-900 text-white py-4 px-8 text-sm">
        <div class="max-w-4xl mx-auto flex justify-between">
            <span>Playback ID: {playback_id}</span>
            <span>Video Cost: ${video_result.get('cost', 0.18):.2f}</span>
            <span>Generation: {video_result.get('generation_time', 0):.1f}s</span>
        </div>
    </div>
</body>
</html>
"""

    return html


# ============================================================
# MAIN
# ============================================================

async def main():
    import sys

    # Check for --use-existing flag
    use_existing = "--use-existing" in sys.argv or "-e" in sys.argv
    existing_playback_id = "a2WovgYswGqojcLdc6Mv8YabXbHsU02MTPHoDbcE700Yc"

    print("\n" + "=" * 70)
    print("  FULL ARTICLE-FIRST WORKFLOW TEST")
    print("  Cyprus Digital Nomad Visa - Complete Article")
    print("=" * 70)

    # Step 1: Article exists (defined above)
    print(f"\n📝 Article: {ARTICLE['title']}")
    print(f"   Sections: {len(ARTICLE['sections'])}")

    if use_existing:
        print(f"\n⚡ Using existing playback_id: {existing_playback_id}")
        mux_result = {"playback_id": existing_playback_id, "asset_id": "existing"}
        video_result = {"cost": 0.18, "generation_time": 0}
    else:
        # Step 2: Generate video prompt from article
        print("\n📋 Generating video prompt from article sections...")
        video_prompt = generate_video_prompt_from_article(ARTICLE)
        print(f"   Prompt: {len(video_prompt)} chars")

        # Step 3: Generate video
        video_result = await generate_video(video_prompt)
        if not video_result:
            print("\n❌ Video generation failed")
            return

        # Step 4: Upload to Mux
        mux_result = await upload_to_mux(video_result["video_url"])
        if not mux_result:
            print("\n❌ Mux upload failed")
            return

    # Step 5: Generate full article HTML
    print("\n" + "=" * 70)
    print("  GENERATING FULL ARTICLE HTML")
    print("=" * 70)

    html = generate_full_article_html(ARTICLE, mux_result["playback_id"], video_result)

    output_path = "/Users/dankeegan/quest/content-worker/test_full_article_demo.html"
    with open(output_path, "w") as f:
        f.write(html)

    print(f"\n✅ Full article saved to: {output_path}")
    print(f"\nOpen in browser: file://{output_path}")

    print("\n" + "=" * 70)
    print("  WORKFLOW COMPLETE!")
    print("=" * 70)
    print(f"\n  Playback ID: {mux_result['playback_id']}")
    print(f"  Video Cost: ${video_result['cost']:.2f}")
    print(f"  Generation Time: {video_result['generation_time']:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
