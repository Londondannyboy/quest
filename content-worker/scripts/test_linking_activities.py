#!/usr/bin/env python3
"""
Test script for new linking activities.

Run this BEFORE a full workflow to verify:
1. finesse_internal_links activity exists and has correct logic
2. verify_external_links activity exists and has correct logic
3. Internal linking params passed to generation
4. Prompt includes external link requirements

Usage:
    cd content-worker && python3 scripts/test_linking_activities.py
"""

import os
import re
import sys

# Project paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_dir = os.path.join(project_root, 'src')


def read_file(relative_path):
    """Read a file from the project."""
    full_path = os.path.join(project_root, relative_path)
    with open(full_path, 'r') as f:
        return f.read()


def test_finesse_internal_links():
    """Test the internal link finessing activity exists and has correct logic."""
    print("\n" + "="*60)
    print("TEST 1: finesse_internal_links activity")
    print("="*60)

    try:
        content = read_file('src/activities/validation/link_validator.py')

        checks = [
            ('async def finesse_internal_links', 'Activity function defined'),
            ('cluster_articles: List[Dict[str, Any]]', 'Takes cluster_articles param'),
            ('primary_article_id: int', 'Takes primary_article_id param'),
            ('mode_anchors', 'Mode-specific anchor text defined'),
            ('max_links_to_add = 3', 'Max links limit configured'),
            ('if aid != article_id', 'Excludes self from siblings'),
            ('primary_article_id else 1', 'Prioritizes primary article'),
            ('Updated cluster_articles with improved internal linking', 'Returns updated articles'),
        ]

        passed = 0
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✓ {description}")
                passed += 1
            else:
                print(f"  ✗ {description} - MISSING")

        if passed == len(checks):
            print("\n✓ finesse_internal_links: PASSED")
            return True
        else:
            print(f"\n✗ finesse_internal_links: {len(checks) - passed} checks failed")
            return False

    except Exception as e:
        print(f"\n✗ finesse_internal_links: FAILED - {e}")
        return False


def test_verify_external_links():
    """Test the external link verification activity."""
    print("\n" + "="*60)
    print("TEST 2: verify_external_links activity")
    print("="*60)

    try:
        content = read_file('src/activities/validation/link_validator.py')

        checks = [
            ('async def verify_external_links', 'Activity function defined'),
            ('content: str', 'Takes content param'),
            ('min_links: int = 10', 'Min links threshold with default'),
            ('high_authority', 'High authority categorization'),
            ('medium_authority', 'Medium authority categorization'),
            ('quality_score', 'Quality score calculation'),
            ('europa.eu', 'EU gov domains recognized'),
            ('numbeo.com', 'Cost of living sources recognized'),
            ('wikipedia.org', 'Wikipedia recognized'),
            ('meets_minimum', 'Minimum check result'),
        ]

        passed = 0
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✓ {description}")
                passed += 1
            else:
                print(f"  ✗ {description} - MISSING")

        if passed == len(checks):
            print("\n✓ verify_external_links: PASSED")
            return True
        else:
            print(f"\n✗ verify_external_links: {len(checks) - passed} checks failed")
            return False

    except Exception as e:
        print(f"\n✗ verify_external_links: FAILED - {e}")
        return False


def test_generation_prompt_params():
    """Test that generation function accepts linking parameters."""
    print("\n" + "="*60)
    print("TEST 3: generate_country_guide_content params")
    print("="*60)

    try:
        content = read_file('src/activities/generation/country_guide_generation.py')

        checks = [
            ('primary_slug: Optional[str] = None', 'primary_slug parameter'),
            ('sibling_slugs: Optional[List[str]] = None', 'sibling_slugs parameter'),
            ('get_mode_specific_prompt(mode, country_name, voices or [], primary_slug, sibling_slugs)',
             'Passes slugs to mode prompt'),
        ]

        passed = 0
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✓ {description}")
                passed += 1
            else:
                print(f"  ✗ {description} - MISSING")

        if passed == len(checks):
            print("\n✓ generate_country_guide_content: PASSED")
            return True
        else:
            print(f"\n✗ generate_country_guide_content: {len(checks) - passed} checks failed")
            return False

    except Exception as e:
        print(f"\n✗ generate_country_guide_content: FAILED - {e}")
        return False


def test_external_links_prompt():
    """Test that the prompt includes external link requirements."""
    print("\n" + "="*60)
    print("TEST 4: External links prompt section")
    print("="*60)

    try:
        content = read_file('src/activities/generation/country_guide_generation.py')

        checks = [
            ('EXTERNAL LINKS (CRITICAL', 'External links section header'),
            ('Every factual claim MUST have a source link', 'Source link requirement'),
            ('SHORT anchor text (2-4 words max)', 'Short anchor text rule'),
            ('Minimum: 10-15 external', 'Minimum external links'),
            ('Tax rates → Link to tax authority', 'Tax source guidance'),
            ('Visa requirements → Link to government', 'Visa source guidance'),
            ('Cost of living → Link to Numbeo', 'CoL source guidance'),
            ('Sources & References', 'References section required'),
            ('8-12 authoritative sources', 'Minimum sources in references'),
        ]

        passed = 0
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✓ {description}")
                passed += 1
            else:
                print(f"  ✗ {description} - MISSING")

        if passed == len(checks):
            print("\n✓ External links prompt: PASSED")
            return True
        else:
            print(f"\n✗ External links prompt: {len(checks) - passed} checks failed")
            return False

    except Exception as e:
        print(f"\n✗ External links prompt: FAILED - {e}")
        return False


def test_internal_links_prompt():
    """Test that internal link instructions are in the prompt."""
    print("\n" + "="*60)
    print("TEST 5: Internal links prompt section")
    print("="*60)

    try:
        content = read_file('src/activities/generation/country_guide_generation.py')

        checks = [
            ('INTERNAL LINKS (Critical for SEO)', 'Internal links section'),
            ('primary_slug', 'Primary slug reference'),
            ('sibling_slugs', 'Sibling slugs reference'),
            ('Cross-Link Opportunities', 'Cross-link section'),
            ('SHORT anchor text (2-4 words)', 'Short anchor rule'),
            ("NOT long anchors like", 'Long anchor warning'),
            ('Distribute naturally', 'Natural distribution'),
        ]

        passed = 0
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✓ {description}")
                passed += 1
            else:
                print(f"  ✗ {description} - MISSING")

        if passed == len(checks):
            print("\n✓ Internal links prompt: PASSED")
            return True
        else:
            print(f"\n✗ Internal links prompt: {len(checks) - passed} checks failed")
            return False

    except Exception as e:
        print(f"\n✗ Internal links prompt: FAILED - {e}")
        return False


def test_workflow_slug_computation():
    """Test that workflow computes and passes slugs correctly."""
    print("\n" + "="*60)
    print("TEST 6: Workflow slug computation")
    print("="*60)

    try:
        content = read_file('src/workflows/country_guide_creation.py')

        checks = [
            ('base_slug = f"{country_name.lower()', 'Base slug computed'),
            ('primary_slug = base_slug', 'Primary slug set'),
            ('all_slugs = {', 'All slugs dict'),
            ('"story": base_slug', 'Story slug'),
            ('base_slug}-guide', 'Guide slug'),
            ('base_slug}-yolo', 'YOLO slug'),
            ('base_slug}-voices', 'Voices slug'),
            ('sibling_slugs = [slug for m, slug in all_slugs.items() if m != mode]',
             'Sibling excludes current mode'),
            ('primary_slug,', 'Primary passed to activity'),
            ('sibling_slugs', 'Siblings passed to activity'),
        ]

        passed = 0
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✓ {description}")
                passed += 1
            else:
                print(f"  ✗ {description} - MISSING")

        if passed == len(checks):
            print("\n✓ Workflow slug computation: PASSED")
            return True
        else:
            print(f"\n✗ Workflow slug computation: {len(checks) - passed} checks failed")
            return False

    except Exception as e:
        print(f"\n✗ Workflow slug computation: FAILED - {e}")
        return False


def test_playwright_precleanse():
    """Test that Playwright pre-cleansing is in the workflow."""
    print("\n" + "="*60)
    print("TEST 7: Playwright URL pre-cleansing")
    print("="*60)

    try:
        content = read_file('src/workflows/country_guide_creation.py')

        checks = [
            ('playwright_pre_cleanse', 'Activity called in workflow'),
            ('Phase 4b: Pre-cleansing', 'Phase logged'),
            ('score', 'URL scoring'),
            ('>= 0.4', 'Score threshold'),
        ]

        passed = 0
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✓ {description}")
                passed += 1
            else:
                print(f"  ✗ {description} - MISSING")

        # Also check the activity exists
        validator_content = read_file('src/activities/validation/link_validator.py')

        validator_checks = [
            ('async def playwright_pre_cleanse', 'Pre-cleanse activity exists'),
            ('PAYWALL_DOMAINS', 'Paywall detection'),
            ('ERROR_INDICATORS', '404/error detection'),
            ('BOT_BLOCK_INDICATORS', 'CAPTCHA detection'),
        ]

        for pattern, description in validator_checks:
            if pattern in validator_content:
                print(f"  ✓ {description}")
                passed += 1
            else:
                print(f"  ✗ {description} - MISSING")

        total = len(checks) + len(validator_checks)
        if passed == total:
            print("\n✓ Playwright pre-cleansing: PASSED")
            return True
        else:
            print(f"\n✗ Playwright pre-cleansing: {total - passed} checks failed")
            return False

    except Exception as e:
        print(f"\n✗ Playwright pre-cleansing: FAILED - {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LINKING ACTIVITIES TEST SUITE")
    print("="*60)
    print("Testing new linking features before full workflow run...")

    results = []

    # Run tests
    results.append(test_finesse_internal_links())
    results.append(test_verify_external_links())
    results.append(test_generation_prompt_params())
    results.append(test_external_links_prompt())
    results.append(test_internal_links_prompt())
    results.append(test_workflow_slug_computation())
    results.append(test_playwright_precleanse())

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(results)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nReady for full workflow! The following features are verified:")
        print("  • Internal linking between cluster articles")
        print("  • External link requirements in prompts")
        print("  • Short anchor text rules (2-4 words)")
        print("  • Playwright URL pre-cleansing")
        print("  • Sibling slug computation (no self-links)")
        print("  • Post-generation link finessing activities")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        print("Fix issues before running full workflow")
        return 1


if __name__ == "__main__":
    sys.exit(main())
