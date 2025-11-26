#!/usr/bin/env python3
"""
Thumbnail Analysis Tool
Generates a visual comparison grid to identify distinct frames across a 12-second video.
Groups thumbnails by act and highlights recommended choices.
"""

import sys

def generate_analysis_html(playback_id: str, output_path: str = None):
    """Generate an HTML page with thumbnail analysis."""

    base_url = f"https://image.mux.com/{playback_id}"

    # Sample at 0.5s intervals for 12 seconds
    timestamps = [i * 0.5 for i in range(25)]  # 0.0 to 12.0

    # Define acts
    acts = [
        {"name": "Act 1: The Grind", "start": 0, "end": 3, "color": "blue"},
        {"name": "Act 2: The Dream", "start": 3, "end": 6, "color": "purple"},
        {"name": "Act 3: The Journey", "start": 6, "end": 9, "color": "amber"},
        {"name": "Act 4: The Reality", "start": 9, "end": 12, "color": "emerald"},
    ]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thumbnail Analysis - {playback_id[:12]}...</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .thumbnail-card {{
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .thumbnail-card:hover {{
            transform: scale(1.05);
            z-index: 10;
        }}
        .thumbnail-card.selected {{
            ring: 4px;
            ring-color: #fbbf24;
        }}
        .act-divider {{
            border-left: 3px solid currentColor;
        }}
    </style>
</head>
<body class="bg-gray-900 text-white p-6">
    <div class="max-w-7xl mx-auto">
        <header class="mb-8">
            <h1 class="text-3xl font-bold mb-2">Thumbnail Analysis</h1>
            <p class="text-gray-400">Click thumbnails to mark as "selected" for use. Identify visually distinct frames.</p>
            <p class="text-sm text-gray-500 mt-2">Playback ID: {playback_id}</p>
        </header>

        <!-- Full Timeline Grid -->
        <section class="mb-12">
            <h2 class="text-xl font-semibold mb-4">Full Timeline (0.5s intervals)</h2>
            <div class="grid grid-cols-6 md:grid-cols-8 lg:grid-cols-12 gap-2">
"""

    for ts in timestamps:
        # Determine which act this timestamp belongs to
        act_idx = min(int(ts // 3), 3)
        act = acts[act_idx]
        border_color = f"border-{act['color']}-500"

        html += f"""
                <div class="thumbnail-card relative" onclick="this.classList.toggle('ring-4'); this.classList.toggle('ring-yellow-400')">
                    <img
                        src="{base_url}/thumbnail.jpg?time={ts}&width=200"
                        alt="{ts}s"
                        class="w-full aspect-video object-cover rounded border-2 {border_color}"
                        loading="lazy"
                    />
                    <div class="absolute bottom-0 left-0 right-0 bg-black/70 text-center py-1 text-xs">
                        {ts}s
                    </div>
                </div>
"""

    html += """
            </div>
        </section>

        <!-- Act-by-Act Analysis -->
        <section class="mb-12">
            <h2 class="text-xl font-semibold mb-4">Act-by-Act Breakdown</h2>
            <div class="space-y-8">
"""

    for act in acts:
        act_timestamps = [ts for ts in timestamps if act["start"] <= ts < act["end"]]

        html += f"""
                <div class="bg-gray-800 rounded-xl p-6">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="w-4 h-4 rounded-full bg-{act['color']}-500"></div>
                        <h3 class="text-lg font-semibold">{act['name']}</h3>
                        <span class="text-gray-400 text-sm">({act['start']}s - {act['end']}s)</span>
                    </div>
                    <div class="grid grid-cols-3 md:grid-cols-6 gap-3">
"""

        for ts in act_timestamps:
            html += f"""
                        <div class="thumbnail-card relative" onclick="this.classList.toggle('ring-4'); this.classList.toggle('ring-yellow-400')">
                            <img
                                src="{base_url}/thumbnail.jpg?time={ts}&width=300"
                                alt="{ts}s"
                                class="w-full aspect-video object-cover rounded-lg"
                                loading="lazy"
                            />
                            <div class="absolute bottom-0 left-0 right-0 bg-black/70 text-center py-1 text-sm font-medium">
                                {ts}s
                            </div>
                        </div>
"""

        html += """
                    </div>
                    <div class="mt-3 text-sm text-gray-400">
                        <strong>Tip:</strong> Look for frames with different compositions, lighting, or subjects within this act.
                    </div>
                </div>
"""

    html += """
            </div>
        </section>

        <!-- Recommended Selection Strategy -->
        <section class="mb-12 bg-gray-800 rounded-xl p-6">
            <h2 class="text-xl font-semibold mb-4">Selection Strategy</h2>
            <div class="grid md:grid-cols-2 gap-6">
                <div>
                    <h3 class="font-semibold text-amber-400 mb-2">For 4 Section Headers</h3>
                    <ul class="text-gray-300 space-y-1 text-sm">
                        <li>• Pick 1 frame from each act's middle (1.5s, 4.5s, 7.5s, 10.5s)</li>
                        <li>• Or pick from transitions for variety</li>
                        <li>• Avoid adjacent timestamps that look identical</li>
                    </ul>
                </div>
                <div>
                    <h3 class="font-semibold text-amber-400 mb-2">For 8 Section Headers</h3>
                    <ul class="text-gray-300 space-y-1 text-sm">
                        <li>• Pick 2 frames per act (early + late)</li>
                        <li>• Example: 1.0s, 2.5s, 4.0s, 5.5s, 7.0s, 8.5s, 10.0s, 11.5s</li>
                        <li>• Stagger to maximize visual variety</li>
                    </ul>
                </div>
            </div>
        </section>

        <!-- Quick Copy URLs -->
        <section class="bg-gray-800 rounded-xl p-6">
            <h2 class="text-xl font-semibold mb-4">Quick Copy URLs</h2>
            <div class="grid md:grid-cols-2 gap-4">
                <div>
                    <h3 class="font-semibold text-sm text-gray-400 mb-2">4-Section Recommended</h3>
                    <div class="space-y-1 text-xs font-mono bg-gray-900 p-3 rounded">
"""

    recommended_4 = [1.5, 4.5, 7.5, 10.5]
    for i, ts in enumerate(recommended_4):
        html += f'                        <div class="truncate">Section {i+1}: {base_url}/thumbnail.jpg?time={ts}&width=800</div>\n'

    html += """
                    </div>
                </div>
                <div>
                    <h3 class="font-semibold text-sm text-gray-400 mb-2">8-Section Recommended</h3>
                    <div class="space-y-1 text-xs font-mono bg-gray-900 p-3 rounded overflow-auto max-h-40">
"""

    recommended_8 = [1.0, 2.5, 4.0, 5.5, 7.0, 8.5, 10.0, 11.5]
    for i, ts in enumerate(recommended_8):
        html += f'                        <div class="truncate">Section {i+1}: {base_url}/thumbnail.jpg?time={ts}&width=800</div>\n'

    html += f"""
                    </div>
                </div>
            </div>
        </section>

        <!-- Large Preview -->
        <section class="mt-12">
            <h2 class="text-xl font-semibold mb-4">Large Preview (hover to compare)</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
"""

    preview_times = [1.5, 4.5, 7.5, 10.5]
    for i, ts in enumerate(preview_times):
        act = acts[i]
        html += f"""
                <div class="relative group">
                    <img
                        src="{base_url}/thumbnail.jpg?time={ts}&width=800"
                        alt="Act {i+1} - {ts}s"
                        class="w-full aspect-video object-cover rounded-xl"
                    />
                    <div class="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent rounded-xl"></div>
                    <div class="absolute bottom-3 left-3">
                        <span class="text-{act['color']}-400 text-sm font-semibold">{act['name']}</span>
                        <p class="text-white text-lg font-bold">{ts}s</p>
                    </div>
                </div>
"""

    html += """
            </div>
        </section>
    </div>

    <script>
        // Track selected thumbnails
        let selected = new Set();

        document.querySelectorAll('.thumbnail-card').forEach(card => {
            card.addEventListener('click', function() {
                const time = this.querySelector('div').textContent.replace('s', '');
                if (selected.has(time)) {
                    selected.delete(time);
                } else {
                    selected.add(time);
                }
                console.log('Selected timestamps:', Array.from(selected).sort((a,b) => a-b));
            });
        });
    </script>
</body>
</html>
"""

    if output_path is None:
        output_path = "/Users/dankeegan/quest/content-worker/thumbnail_analysis.html"

    with open(output_path, "w") as f:
        f.write(html)

    print(f"Analysis saved to: {output_path}")
    print(f"Open: file://{output_path}")

    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use existing playback_id as default
        playback_id = "a2WovgYswGqojcLdc6Mv8YabXbHsU02MTPHoDbcE700Yc"
        print(f"Using default playback_id: {playback_id}")
    else:
        playback_id = sys.argv[1]

    generate_analysis_html(playback_id)
