#!/usr/bin/env python3
"""
Test script for app configuration system
"""

import sys
sys.path.insert(0, '/Users/dankeegan/quest')

from worker.config import get_app_config, AVAILABLE_APPS


def test_app_configs():
    """Test loading and displaying app configurations"""

    print("=" * 80)
    print("QUEST App Configuration System Test")
    print("=" * 80)
    print()

    print(f"Available apps: {', '.join(AVAILABLE_APPS)}")
    print()

    for app_name in AVAILABLE_APPS:
        print("=" * 80)
        print(f"Testing: {app_name.upper()}")
        print("=" * 80)

        try:
            config = get_app_config(app_name)

            print(f"\n✅ Successfully loaded config for '{app_name}'")
            print()
            print(f"Display Name: {config.display_name}")
            print(f"Domain: {config.domain}")
            print(f"Target Audience: {config.target_audience}")
            print(f"Tone: {config.tone[:80]}...")
            print(f"Content Focus: {config.content_focus[:80]}...")
            print()
            print(f"Word Count Range: {config.word_count_range[0]:,} - {config.word_count_range[1]:,} words")
            print(f"Min Sections: {config.min_sections}")
            print(f"Min Citations: {config.min_citations}")
            print()
            print(f"Quality Thresholds:")
            print(f"  - Min Quality Score: {config.min_quality_score}")
            print(f"  - Auto-Publish Threshold: {config.auto_publish_threshold}")
            print()
            print(f"Writing Guidelines ({len(config.writing_guidelines)} items):")
            for i, guideline in enumerate(config.writing_guidelines[:3], 1):
                print(f"  {i}. {guideline[:70]}...")
            if len(config.writing_guidelines) > 3:
                print(f"  ... and {len(config.writing_guidelines) - 3} more")
            print()
            print(f"Content Requirements ({len(config.content_requirements)} items):")
            for i, req in enumerate(config.content_requirements[:3], 1):
                print(f"  {i}. {req[:70]}...")
            if len(config.content_requirements) > 3:
                print(f"  ... and {len(config.content_requirements) - 3} more")
            print()
            print(f"Preferred Sources: {', '.join(config.preferred_sources[:5])}")
            print()
            print(f"Image Style: {config.image_style[:80]}...")
            print()
            print(f"Brand Voice:")
            print(f"  DO: {config.brand_voice.get('do', 'N/A')[:70]}...")
            print(f"  DON'T: {config.brand_voice.get('dont', 'N/A')[:70]}...")
            print()

        except Exception as e:
            print(f"❌ Failed to load config for '{app_name}': {e}")
            return False

    print("=" * 80)
    print("Testing: Invalid App Name")
    print("=" * 80)
    print()

    try:
        config = get_app_config("nonexistent_app")
        print("❌ Should have raised ValueError for invalid app name")
        return False
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {e}")

    print()
    print("=" * 80)
    print("✅ ALL TESTS PASSED")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = test_app_configs()
    sys.exit(0 if success else 1)
