import streamlit as st
import requests
import os
import json
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GATEWAY_URL = os.getenv("GATEWAY_URL", "https://quest-gateway-production.up.railway.app")
API_KEY = os.getenv("API_KEY", "")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
ZEP_API_KEY = os.getenv("ZEP_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Graph mappings for Zep
GRAPH_MAPPING = {
    "placement": os.getenv("ZEP_GRAPH_ID_FINANCE", "finance-knowledge"),
    "pe_news": os.getenv("ZEP_GRAPH_ID_FINANCE", "finance-knowledge"),
    "finance": os.getenv("ZEP_GRAPH_ID_FINANCE", "finance-knowledge"),
    "relocation": os.getenv("ZEP_GRAPH_ID_RELOCATION", "relocation"),
    "jobs": os.getenv("ZEP_GRAPH_ID_JOBS", "jobs"),
    "recruiter": os.getenv("ZEP_GRAPH_ID_JOBS", "jobs"),
}

# Page config
st.set_page_config(
    page_title="Quest Content Creator",
    page_icon="🚀",
    layout="centered"
)

# ===== PASSWORD PROTECTION =====
def check_password():
    """Check if user is authenticated."""
    if not DASHBOARD_PASSWORD:
        # No password set, allow access
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Show login form
    st.title("🔐 Quest Dashboard Login")
    password = st.text_input("Password", type="password", key="password_input")

    if st.button("Login", type="primary"):
        if password == DASHBOARD_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")

    return False

# Check authentication before showing dashboard
if not check_password():
    st.stop()

# Header
st.title("🚀 Quest Content Creator")
st.markdown("*AI-powered company profiles and articles*")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    st.text(f"Gateway: {GATEWAY_URL.split('//')[1][:30]}...")
    if API_KEY:
        st.success("✅ API Key configured")
    else:
        st.warning("⚠️ Set API_KEY in .env file")

    st.divider()
    st.caption("Powered by Temporal + Gemini 2.5 Flash")

# Main navigation tabs
tab_company, tab_article, tab_country, tab_video_enrich, tab_zep, tab_new_worker = st.tabs(["🏢 Company Profile", "📝 Article Creation", "🌍 Country Guide", "🎬 Video Enrichment", "🧠 Zep Facts", "🧪 New Worker"])

# ===== COMPANY PROFILE TAB =====
with tab_company:
    st.subheader("Create Company Profile")

    # Company URL (required)
    url = st.text_input(
        "Company Website URL *",
        placeholder="https://acme.com",
        help="The company's official website",
        key="company_url"
    )

    # App selection
    company_app = st.selectbox(
        "App Context *",
        ["placement", "relocation", "chief-of-staff", "gtm", "newsroom"],
        index=0,
        help="Which app is this profile for?",
        key="company_app"
    )

    # Category
    category = st.selectbox(
        "Company Category *",
        [
            "placement_agent",
            "relocation_provider",
            "recruiter",
            "investment_bank",
            "private_equity_firm",
            "advisory_firm",
            "asset_manager",
            "hedge_fund",
            "consulting_firm",
            "search_firm",
            "other"
        ],
        index=0,
        help="Primary business category"
    )

    # Jurisdiction (required)
    company_jurisdiction = st.selectbox(
        "Jurisdiction *",
        ["UK", "US", "EU", "SG", "AU", "CA", "HK", "AE"],
        index=0,
        help="Geographic focus for research",
        key="company_jurisdiction"
    )

    # Options
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        research_depth = st.selectbox(
            "Research Depth",
            ["quick", "standard", "deep"],
            index=1,
            help="How thorough should the research be?"
        )

    with col2:
        force_update = st.checkbox(
            "Force Update",
            value=False,
            help="Re-research even if company exists"
        )

    # Submit button
    st.divider()

    if st.button("✨ Create Company Profile", type="primary", use_container_width=True, key="create_company"):
        # Validation
        if not url:
            st.error("❌ Please provide a company URL")
        elif not url.startswith(("http://", "https://")):
            st.error("❌ URL must start with http:// or https://")
        else:
            # Show progress
            with st.spinner("🚀 Creating company profile... This takes 5-12 minutes"):
                try:
                    # Call Gateway API
                    response = requests.post(
                        f"{GATEWAY_URL}/v1/workflows/content-worker",
                        headers={
                            "Content-Type": "application/json",
                            "X-API-Key": API_KEY
                        },
                        json={
                            "url": url,
                            "category": category,
                            "jurisdiction": company_jurisdiction,
                            "app": company_app,
                            "force_update": force_update,
                            "research_depth": research_depth
                        },
                        timeout=30
                    )

                    # Handle response
                    if response.status_code == 200 or response.status_code == 201:
                        data = response.json()

                        # Success message
                        st.success("✅ **Workflow Started Successfully!**")

                        # Workflow details
                        st.info(f"**Workflow ID:**\n```\n{data['workflow_id']}\n```")

                        if "company_name" in data and data["company_name"]:
                            st.info(f"**Company:** {data['company_name']}")

                        st.info(f"**Status:** {data.get('status', 'started').upper()}")

                        if "message" in data:
                            st.info(f"**Timeline:** {data['message']}")

                        # Temporal link
                        temporal_url = f"https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows/{data['workflow_id']}"
                        st.markdown(f"### [📊 Monitor in Temporal UI]({temporal_url})")

                        # Instructions
                        st.divider()
                        st.markdown("""
                        **Next Steps:**
                        1. Click the Temporal link above to monitor progress
                        2. Workflow takes 5-12 minutes to complete
                        3. Check your database for the new company profile
                        """)

                    else:
                        # Error response
                        st.error(f"❌ **Error {response.status_code}**")

                        try:
                            error_data = response.json()
                            st.code(error_data, language="json")
                        except:
                            st.text(response.text)

                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. The workflow may still have started - check Temporal UI.")

                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Could not connect to Gateway at {GATEWAY_URL}")
                    st.info("Check that the Gateway URL is correct and the service is running.")

                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
                    st.code(str(e), language="text")

# ===== ARTICLE CREATION TAB =====
with tab_article:
    st.subheader("Create Article")
    st.markdown("*Generate AI-powered articles with research and images*")

    # Topic (required)
    topic = st.text_input(
        "Article Topic *",
        placeholder="Goldman Sachs acquires AI startup for $500M",
        help="The main topic or headline for the article",
        key="article_topic"
    )

    # Article type
    article_type = st.selectbox(
        "Article Type *",
        ["news", "guide", "comparison"],
        index=0,
        help="news: Current events, deals, announcements\nguide: How-to, explanatory content\ncomparison: Top 10, rankings, comparisons",
        key="article_type"
    )

    # App context
    article_app = st.selectbox(
        "App Context *",
        ["placement", "relocation", "chief-of-staff", "gtm", "newsroom"],
        index=0,
        help="Which app is this article for?",
        key="article_app"
    )

    # Jurisdiction
    article_jurisdiction = st.selectbox(
        "Jurisdiction",
        ["UK", "US", "EU", "SG", "AU", "CA", "HK", "AE"],
        index=0,
        help="Geographic focus for research",
        key="article_jurisdiction"
    )

    # Custom slug (optional - for SEO)
    custom_slug = st.text_input(
        "Custom URL Slug (optional)",
        placeholder="my-article-title",
        help="Leave empty to auto-generate from title. Use for SEO or fixing broken Google-indexed URLs.",
        key="article_slug"
    )

    # Options
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        target_word_count = st.slider(
            "Target Word Count",
            min_value=1000,
            max_value=5000,
            value=2000,
            step=500,
            help="Target length of the article (4-act structure works best with 1500-3000 words)"
        )

        num_research_sources = st.slider(
            "Research Sources",
            min_value=5,
            max_value=20,
            value=12,
            step=1,
            help="Number of web sources to crawl for research context"
        )

    with col2:
        # Video - simplified for 4-Act (always 720p, single 12s video)
        generate_video = st.checkbox(
            "Generate 4-Act Video",
            value=True,
            help="12-second cinematic video with 4 acts (3s each). Thumbnails extracted for article sections."
        )

        if generate_video:
            video_quality = "medium"  # Always 720p for 4-Act
            video_count = 1  # Single hero video, thumbnails extracted for sections

            video_model = st.selectbox(
                "Video Model",
                ["seedance", "wan-2.5"],
                index=0,
                help="seedance: Fast, good motion ($0.075)\nwan-2.5: Better depth/parallax, slower ($0.12)",
                key="video_model"
            )

            # Character Style - organized as 2-level selection
            st.markdown("**Character Demographics**")
            character_region = st.selectbox(
                "Region",
                [
                    "Auto (from context)",
                    "None (abstract visuals)",
                    "North European",
                    "South European",
                    "East Asian",
                    "Southeast Asian",
                    "South Asian",
                    "Middle Eastern",
                    "Black",
                    "Diverse"
                ],
                index=0,
                help="Geographic/ethnic context for people in video. 'Auto' lets AI infer from article content.",
                key="character_region"
            )

            # Show gender/type selector only if region is selected (not Auto/None/Diverse)
            if character_region not in ["Auto (from context)", "None (abstract visuals)", "Diverse"]:
                character_type = st.selectbox(
                    "Type",
                    ["Group (mixed gender)", "Male", "Female"],
                    index=0,
                    help="Individual protagonist or group scene",
                    key="character_type"
                )
            else:
                character_type = "Group (mixed gender)"

            # Map to CharacterStyle enum value
            def get_character_style():
                if character_region == "Auto (from context)":
                    return None  # Let app default / Sonnet infer
                elif character_region == "None (abstract visuals)":
                    return "none"
                elif character_region == "Diverse":
                    return "diverse"
                else:
                    # Map region to enum prefix
                    region_map = {
                        "North European": "north_european",
                        "South European": "south_european",
                        "East Asian": "east_asian",
                        "Southeast Asian": "southeast_asian",
                        "South Asian": "south_asian",
                        "Middle Eastern": "middle_eastern",
                        "Black": "black"
                    }
                    prefix = region_map.get(character_region, "diverse")

                    # Map type to suffix
                    if character_type == "Male":
                        return f"{prefix}_male"
                    elif character_type == "Female":
                        return f"{prefix}_female"
                    else:
                        return f"{prefix}_group"

            character_style = get_character_style()
        else:
            video_quality = None
            video_model = "seedance"
            video_count = 0
            character_style = None

        # Note: Content images removed - 4-Act extracts thumbnails from video
        generate_images = False
        content_images_count = 0

    # Custom Video Prompt (only show if video enabled)
    if generate_video:
        st.divider()
        st.markdown("**Video Prompt** *(optional - leave empty for auto-generated)*")

        # Generate default prompt based on topic and app
        default_prompt = f"A professional scene related to {topic if topic else 'business'}, cinematic lighting, smooth camera movement"
        if article_app == "relocation":
            default_prompt = f"A young professional walking through a modern city with international flags and global landmarks, representing relocation and new beginnings, cinematic lighting"
        elif article_app == "placement":
            default_prompt = f"A modern financial district with skyscrapers and professional atmosphere, representing investment banking and private placements, cinematic lighting"

        video_prompt = st.text_area(
            "Custom Prompt",
            value="",
            placeholder=default_prompt,
            help="Leave empty for auto-generated. Short hints (e.g., 'Cyprus beach sunset') will be expanded into full cinematic prompts. 60+ word prompts used verbatim.",
            key="video_prompt",
            height=100
        )
    else:
        video_prompt = ""

    # Cost estimate - simplified for 4-Act
    st.divider()
    research_cost = 0.08  # Serper + Exa
    ai_cost = 0.02  # Claude for article generation
    video_cost = 0.075 if generate_video else 0  # 720p Seedance

    estimated_cost = research_cost + ai_cost + video_cost

    st.caption(f"💰 **Estimated cost:** ${estimated_cost:.2f}")

    # Time estimate
    time_estimate = "5-7 minutes" if generate_video else "2-3 minutes"
    st.caption(f"⏱️ **Estimated time:** {time_estimate}")

    if generate_video:
        st.caption("📹 4-Act video + thumbnails extracted for sections")

    # Submit button
    st.divider()

    if st.button("📝 Create Article", type="primary", use_container_width=True, key="create_article"):
        # Validation
        if not topic:
            st.error("❌ Please provide an article topic")
        elif len(topic) < 10:
            st.error("❌ Topic should be at least 10 characters")
        else:
            # Show progress
            with st.spinner(f"📝 Creating article... This takes {time_estimate}"):
                try:
                    # Call Gateway API for article creation
                    # Build request payload
                    request_payload = {
                        "topic": topic,
                        "article_type": article_type,
                        "app": article_app,
                        "target_word_count": target_word_count,
                        "jurisdiction": article_jurisdiction,
                        "num_research_sources": num_research_sources,
                        # 4-Act video settings
                        "video_quality": video_quality,  # "medium" (720p) or None
                        "video_model": video_model if generate_video else None,
                        "video_prompt": video_prompt if video_prompt.strip() else None,
                        "video_count": video_count,
                        "character_style": character_style,  # Demographics (None = auto from context)
                        # Legacy fields (kept for backwards compatibility)
                        "generate_images": False,
                        "content_images_count": 0
                    }

                    # Add custom slug if provided
                    if custom_slug and custom_slug.strip():
                        request_payload["slug"] = custom_slug.strip()

                    response = requests.post(
                        f"{GATEWAY_URL}/v1/workflows/article-creation",
                        headers={
                            "Content-Type": "application/json",
                            "X-API-Key": API_KEY
                        },
                        json=request_payload,
                        timeout=30
                    )

                    # Handle response
                    if response.status_code == 200 or response.status_code == 201:
                        data = response.json()

                        # Success message
                        st.success("✅ **Article Workflow Started!**")

                        # Workflow details
                        st.info(f"**Workflow ID:**\n```\n{data['workflow_id']}\n```")

                        st.info(f"**Topic:** {topic}")
                        st.info(f"**Type:** {article_type.upper()}")
                        st.info(f"**Target:** {target_word_count} words")

                        if "message" in data:
                            st.info(f"**Timeline:** {data['message']}")

                        # Temporal link
                        temporal_url = f"https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows/{data['workflow_id']}"
                        st.markdown(f"### [📊 Monitor in Temporal UI]({temporal_url})")

                        # Instructions
                        st.divider()
                        steps = """
                        **What's happening:**
                        1. 🔍 Researching topic (Serper + Exa)
                        2. 📥 Crawling discovered URLs (Crawl4AI)
                        3. 🧠 Querying Zep knowledge graph
                        4. ✍️ Generating article content (Haiku)"""

                        step_num = 5
                        if video_quality != "None":
                            steps += f"\n                        {step_num}. 📹 Generating video (Seedance + Mux)"
                            step_num += 1
                        if content_images_count > 0:
                            steps += f"\n                        {step_num}. 🎨 Generating {content_images_count} images (Flux Kontext)"

                        steps += f"\n\n                        **Estimated time:** {time_estimate}"

                        st.markdown(steps)

                    else:
                        # Error response
                        st.error(f"❌ **Error {response.status_code}**")

                        try:
                            error_data = response.json()
                            st.code(error_data, language="json")
                        except:
                            st.text(response.text)

                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. The workflow may still have started - check Temporal UI.")

                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Could not connect to Gateway at {GATEWAY_URL}")
                    st.info("Check that the Gateway URL is correct and the service is running.")

                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
                    st.code(str(e), language="text")

# ===== COUNTRY GUIDE TAB =====
with tab_country:
    st.subheader("Create Country Relocation Guide")
    st.markdown("*Comprehensive guide covering all 8 relocation motivations*")

    # Pre-populated country list with codes and languages
    COUNTRIES = {
        "Portugal (PT)": {"code": "PT", "language": "Portuguese, English"},
        "Spain (ES)": {"code": "ES", "language": "Spanish, English"},
        "Cyprus (CY)": {"code": "CY", "language": "Greek, Turkish, English"},
        "Malta (MT)": {"code": "MT", "language": "Maltese, English"},
        "Greece (GR)": {"code": "GR", "language": "Greek, English"},
        "Italy (IT)": {"code": "IT", "language": "Italian, English"},
        "France (FR)": {"code": "FR", "language": "French, English"},
        "Netherlands (NL)": {"code": "NL", "language": "Dutch, English"},
        "Germany (DE)": {"code": "DE", "language": "German, English"},
        "Ireland (IE)": {"code": "IE", "language": "English, Irish"},
        "Switzerland (CH)": {"code": "CH", "language": "German, French, Italian, English"},
        "Monaco (MC)": {"code": "MC", "language": "French, English"},
        "Andorra (AD)": {"code": "AD", "language": "Catalan, Spanish, French"},
        "United Arab Emirates (AE)": {"code": "AE", "language": "Arabic, English"},
        "Qatar (QA)": {"code": "QA", "language": "Arabic, English"},
        "Bahrain (BH)": {"code": "BH", "language": "Arabic, English"},
        "Saudi Arabia (SA)": {"code": "SA", "language": "Arabic, English"},
        "Oman (OM)": {"code": "OM", "language": "Arabic, English"},
        "Thailand (TH)": {"code": "TH", "language": "Thai, English"},
        "Malaysia (MY)": {"code": "MY", "language": "Malay, English"},
        "Singapore (SG)": {"code": "SG", "language": "English, Mandarin, Malay, Tamil"},
        "Indonesia (ID)": {"code": "ID", "language": "Indonesian, English"},
        "Vietnam (VN)": {"code": "VN", "language": "Vietnamese, English"},
        "Philippines (PH)": {"code": "PH", "language": "Filipino, English"},
        "Japan (JP)": {"code": "JP", "language": "Japanese, English"},
        "South Korea (KR)": {"code": "KR", "language": "Korean, English"},
        "Taiwan (TW)": {"code": "TW", "language": "Mandarin, English"},
        "Hong Kong (HK)": {"code": "HK", "language": "Cantonese, English, Mandarin"},
        "Australia (AU)": {"code": "AU", "language": "English"},
        "New Zealand (NZ)": {"code": "NZ", "language": "English, Māori"},
        "Canada (CA)": {"code": "CA", "language": "English, French"},
        "United States (US)": {"code": "US", "language": "English, Spanish"},
        "Mexico (MX)": {"code": "MX", "language": "Spanish, English"},
        "Costa Rica (CR)": {"code": "CR", "language": "Spanish, English"},
        "Panama (PA)": {"code": "PA", "language": "Spanish, English"},
        "Belize (BZ)": {"code": "BZ", "language": "English, Spanish"},
        "Colombia (CO)": {"code": "CO", "language": "Spanish, English"},
        "Brazil (BR)": {"code": "BR", "language": "Portuguese, English"},
        "Argentina (AR)": {"code": "AR", "language": "Spanish, English"},
        "Uruguay (UY)": {"code": "UY", "language": "Spanish, English"},
        "Chile (CL)": {"code": "CL", "language": "Spanish, English"},
        "Mauritius (MU)": {"code": "MU", "language": "English, French, Creole"},
        "South Africa (ZA)": {"code": "ZA", "language": "English, Afrikaans, Zulu"},
        "Morocco (MA)": {"code": "MA", "language": "Arabic, French, English"},
        "Egypt (EG)": {"code": "EG", "language": "Arabic, English"},
        "St Kitts and Nevis (KN)": {"code": "KN", "language": "English"},
        "Antigua and Barbuda (AG)": {"code": "AG", "language": "English"},
        "Dominica (DM)": {"code": "DM", "language": "English"},
        "Grenada (GD)": {"code": "GD", "language": "English"},
        "Barbados (BB)": {"code": "BB", "language": "English"},
        "Cayman Islands (KY)": {"code": "KY", "language": "English"},
        "British Virgin Islands (VG)": {"code": "VG", "language": "English"},
    }

    # Country dropdown
    selected_country = st.selectbox(
        "Select Country *",
        options=list(COUNTRIES.keys()),
        index=0,
        help="Choose a country for the relocation guide",
        key="country_select"
    )

    # Extract country info
    country_info = COUNTRIES[selected_country]
    country_code = country_info["code"]
    country_name = selected_country.split(" (")[0]  # "Portugal (PT)" -> "Portugal"
    country_language = country_info["language"]

    # Show selected info
    st.caption(f"📍 **{country_name}** | Code: `{country_code}` | Languages: {country_language}")

    # Relocation Motivations
    st.divider()
    st.markdown("**Relocation Motivations** *(select all that apply)*")

    all_motivations = [
        ("corporate", "💼 Corporate", "Business setup, corporate tax"),
        ("trust", "🛡️ Trust", "Asset protection, trusts"),
        ("wealth", "💎 Wealth", "Wealth management, private banking"),
        ("retirement", "🌅 Retirement", "Retirement visas, pension"),
        ("digital-nomad", "💻 Digital Nomad", "Remote work visas"),
        ("lifestyle", "🌴 Lifestyle", "Quality of life, climate"),
        ("new-start", "🚀 New Start", "Fresh beginning, escape"),
        ("family", "👨‍👩‍👧‍👦 Family", "Family relocation, schools"),
    ]

    selected_motivations = []
    cols = st.columns(4)
    for i, (key, label, desc) in enumerate(all_motivations):
        with cols[i % 4]:
            if st.checkbox(label, value=True, help=desc, key=f"mot_{key}"):
                selected_motivations.append(key)

    # Tags (optional)
    st.divider()
    tags_input = st.text_input(
        "Tags (optional)",
        placeholder="eu-member, schengen, english-speaking",
        help="Comma-separated tags for the country",
        key="country_tags"
    )

    # Video option
    st.divider()
    st.markdown("**Video Settings**")

    generate_country_video = st.checkbox(
        "Generate 4-Act Video (Seedance)",
        value=True,
        help="12-second cinematic video using Seedance model. Thumbnails extracted for article sections.",
        key="country_video"
    )

    if generate_country_video:
        country_video_quality = st.radio(
            "Resolution",
            ["480p (fast, ~$0.05)", "720p (recommended, ~$0.08)", "1080p (slow, ~$0.12)"],
            index=1,
            horizontal=True,
            key="country_video_quality"
        )
        # Map display to actual value
        quality_map = {"480p (fast, ~$0.05)": "low", "720p (recommended, ~$0.08)": "medium", "1080p (slow, ~$0.12)": "high"}
        country_video_quality = quality_map[country_video_quality]
    else:
        country_video_quality = None

    # Guide length (simplified - just use default 4000 words for comprehensive guide)
    country_word_count = 4000

    # Cost/time estimate
    st.divider()
    video_cost = {"low": 0.05, "medium": 0.08, "high": 0.12}.get(country_video_quality, 0)
    total_cost = 0.10 + video_cost  # Research + AI + video
    st.caption(f"💰 **Estimated cost:** ${total_cost:.2f}")
    st.caption("⏱️ **Estimated time:** 8-15 minutes")
    st.caption("📋 **Outputs:** ~4,000 word guide + 4-act video + Country facts")

    # Submit button
    st.divider()

    if st.button("🌍 Create Country Guide", type="primary", use_container_width=True, key="create_country"):
        # Validation
        if not country_name:
            st.error("❌ Please provide a country name")
        elif not country_code or len(country_code) != 2:
            st.error("❌ Please provide a valid 2-letter country code")
        elif not selected_motivations:
            st.error("❌ Please select at least one motivation")
        else:
            # Show progress
            with st.spinner("🌍 Creating country guide... This takes 8-15 minutes"):
                try:
                    # Parse tags
                    tags = [t.strip() for t in tags_input.split(",")] if tags_input else None

                    # Build request payload
                    request_payload = {
                        "country_name": country_name,
                        "country_code": country_code.upper(),
                        "app": "relocation",
                        "language": country_language if country_language else None,
                        "relocation_motivations": selected_motivations,
                        "relocation_tags": tags,
                        "video_quality": country_video_quality,
                        "target_word_count": country_word_count,
                    }

                    response = requests.post(
                        f"{GATEWAY_URL}/v1/workflows/country-guide",
                        headers={
                            "Content-Type": "application/json",
                            "X-API-Key": API_KEY
                        },
                        json=request_payload,
                        timeout=30
                    )

                    # Handle response
                    if response.status_code == 200 or response.status_code == 201:
                        data = response.json()

                        # Success message
                        st.success("✅ **Country Guide Workflow Started!**")

                        # Workflow details
                        st.info(f"**Workflow ID:**\n```\n{data['workflow_id']}\n```")

                        st.info(f"**Country:** {country_name} ({country_code.upper()})")
                        st.info(f"**Motivations:** {len(selected_motivations)} selected")

                        if "message" in data:
                            st.info(f"**Timeline:** {data['message']}")

                        # Temporal link
                        temporal_url = f"https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows/{data['workflow_id']}"
                        st.markdown(f"### [📊 Monitor in Temporal UI]({temporal_url})")

                        # Instructions
                        st.divider()
                        st.markdown("""
                        **What's happening:**
                        1. 📊 SEO Research (DataForSEO keywords)
                        2. 🔍 Authoritative Research (Exa + DataForSEO)
                        3. 📥 Crawling discovered URLs
                        4. 🧠 Querying Zep knowledge graph
                        5. ✍️ Generating 8-motivation guide
                        6. 💾 Saving article & updating country facts
                        7. 📹 Generating 4-act video
                        8. ✅ Publishing guide

                        **Expected time:** 8-15 minutes
                        """)

                    else:
                        # Error response
                        st.error(f"❌ **Error {response.status_code}**")

                        try:
                            error_data = response.json()
                            st.code(error_data, language="json")
                        except:
                            st.text(response.text)

                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. The workflow may still have started - check Temporal UI.")

                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Could not connect to Gateway at {GATEWAY_URL}")
                    st.info("Check that the Gateway URL is correct and the service is running.")

                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
                    st.code(str(e), language="text")

# ===== ZEP FACTS TAB =====
with tab_zep:
    st.subheader("Zep Knowledge Graph Facts")
    st.markdown("*Search, review, and manage facts in the knowledge graph*")

    # Check if Zep is configured
    if not ZEP_API_KEY:
        st.warning("⚠️ ZEP_API_KEY not configured. Add it to your .env file.")
        st.stop()

    # Sub-tabs for different operations
    zep_subtab1, zep_subtab2, zep_subtab3 = st.tabs(["🔍 Search Facts", "📄 Article Facts", "🗑️ Delete Facts"])

    # ===== SEARCH FACTS SUB-TAB =====
    with zep_subtab1:
        st.markdown("### Search Knowledge Graph")

        col1, col2 = st.columns([3, 1])

        with col1:
            search_query = st.text_input(
                "Search Query",
                placeholder="Evercore investment banking",
                help="Search for facts in the knowledge graph",
                key="zep_search_query"
            )

        with col2:
            search_graph = st.selectbox(
                "Graph",
                list(set(GRAPH_MAPPING.values())),
                index=0,
                help="Which knowledge graph to search",
                key="zep_search_graph"
            )

        search_limit = st.slider("Max Results", 5, 50, 20, key="zep_search_limit")

        if st.button("🔍 Search", type="primary", key="zep_search_btn"):
            if not search_query:
                st.error("Please enter a search query")
            else:
                with st.spinner("Searching knowledge graph..."):
                    try:
                        from zep_cloud.client import AsyncZep

                        async def search_facts():
                            client = AsyncZep(api_key=ZEP_API_KEY)
                            results = await client.graph.search(
                                graph_id=search_graph,
                                query=search_query,
                                scope="edges",
                                reranker="cross_encoder",
                                limit=search_limit
                            )
                            return results

                        results = asyncio.run(search_facts())

                        if not results.edges:
                            st.info("No facts found for this query.")
                        else:
                            st.success(f"Found {len(results.edges)} facts")

                            # Store results in session state for potential deletion
                            st.session_state.zep_search_results = results.edges

                            for i, edge in enumerate(results.edges, 1):
                                uuid = getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', 'N/A')
                                fact = getattr(edge, 'fact', 'N/A')
                                valid_at = getattr(edge, 'valid_at', None)
                                invalid_at = getattr(edge, 'invalid_at', None)
                                name = getattr(edge, 'name', 'N/A')

                                # Format dates
                                valid_str = str(valid_at)[:10] if valid_at else "Unknown"
                                status = "🟢 Current" if invalid_at is None else f"🔴 Invalid"

                                with st.expander(f"{i}. {fact[:80]}..." if len(fact) > 80 else f"{i}. {fact}"):
                                    st.markdown(f"**Fact:** {fact}")
                                    st.markdown(f"**Status:** {status}")
                                    st.markdown(f"**Type:** `{name}`")
                                    st.markdown(f"**Valid From:** {valid_str}")
                                    st.code(uuid, language="text")
                                    st.caption("☝️ Copy UUID to delete this fact")

                    except Exception as e:
                        st.error(f"Error searching: {str(e)}")

    # ===== ARTICLE FACTS SUB-TAB =====
    with zep_subtab2:
        st.markdown("### View Facts Used in Article")

        if not DATABASE_URL:
            st.warning("⚠️ DATABASE_URL not configured. Add it to your .env file.")
        else:
            article_id_input = st.text_input(
                "Article ID",
                placeholder="123",
                help="Enter the article ID to view facts used",
                key="zep_article_id"
            )

            if st.button("📄 Load Article Facts", type="primary", key="zep_article_btn"):
                if not article_id_input:
                    st.error("Please enter an article ID")
                else:
                    with st.spinner("Loading article facts..."):
                        try:
                            import psycopg

                            async def get_article_facts():
                                async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
                                    async with conn.cursor() as cur:
                                        await cur.execute("""
                                            SELECT title, slug, zep_facts, created_at
                                            FROM articles
                                            WHERE id = %s
                                        """, (article_id_input,))
                                        return await cur.fetchone()

                            result = asyncio.run(get_article_facts())

                            if not result:
                                st.error(f"Article not found: {article_id_input}")
                            else:
                                title, slug, zep_facts, created_at = result

                                st.success(f"**{title}**")
                                st.caption(f"Slug: `{slug}` | Created: {created_at}")

                                if not zep_facts:
                                    st.info("No Zep facts stored for this article.")
                                else:
                                    facts = json.loads(zep_facts) if isinstance(zep_facts, str) else zep_facts
                                    st.markdown(f"**{len(facts)} facts used:**")

                                    for i, fact_obj in enumerate(facts, 1):
                                        if isinstance(fact_obj, dict):
                                            fact = fact_obj.get("fact", "N/A")
                                            uuid = fact_obj.get("uuid", "N/A")
                                            valid_at = fact_obj.get("valid_at")
                                            invalid_at = fact_obj.get("invalid_at")
                                            name = fact_obj.get("name", "N/A")

                                            status = "🟢" if invalid_at is None else "🔴"
                                            valid_str = str(valid_at)[:10] if valid_at else "Unknown"

                                            with st.expander(f"{status} {i}. {fact[:60]}..."):
                                                st.markdown(f"**Fact:** {fact}")
                                                st.markdown(f"**Type:** `{name}`")
                                                st.markdown(f"**Valid From:** {valid_str}")
                                                st.code(uuid, language="text")
                                        else:
                                            st.markdown(f"{i}. {fact_obj}")

                        except Exception as e:
                            st.error(f"Error: {str(e)}")

    # ===== DELETE FACTS SUB-TAB =====
    with zep_subtab3:
        st.markdown("### Delete Fact from Knowledge Graph")
        st.warning("⚠️ **Caution:** Deleting facts is permanent and cannot be undone.")

        delete_uuid = st.text_input(
            "Fact UUID to Delete",
            placeholder="abc123-def456-...",
            help="Paste the UUID of the fact you want to delete",
            key="zep_delete_uuid"
        )

        # Confirmation
        confirm_delete = st.checkbox(
            "I understand this action cannot be undone",
            key="zep_delete_confirm"
        )

        if st.button("🗑️ Delete Fact", type="primary", disabled=not confirm_delete, key="zep_delete_btn"):
            if not delete_uuid:
                st.error("Please enter a fact UUID")
            elif not confirm_delete:
                st.error("Please confirm you understand this action cannot be undone")
            else:
                with st.spinner("Deleting fact..."):
                    try:
                        from zep_cloud.client import AsyncZep

                        async def delete_fact():
                            client = AsyncZep(api_key=ZEP_API_KEY)
                            await client.graph.edge.delete(uuid_=delete_uuid)
                            return True

                        asyncio.run(delete_fact())
                        st.success(f"✅ Fact deleted: `{delete_uuid}`")

                    except Exception as e:
                        st.error(f"Error deleting fact: {str(e)}")

# ===== VIDEO ENRICHMENT TAB =====
with tab_video_enrich:
    st.subheader("Enrich Article with Videos")
    st.markdown("*Analyze article and add hero video + 4-act videos to sections*")

    st.info("📹 This tool will:\n- Ensure hero video is present\n- Generate 12-second 4-act video from article content\n- Cut video into 4 sections using MUX\n- Insert videos into key sections\n- Add thumbnails to remaining sections")

    # Article URL (required)
    article_url = st.text_input(
        "Article URL or Slug *",
        placeholder="https://relocation.quest/articles/moving-to-portugal or just 'moving-to-portugal'",
        help="Full URL or just the slug of the article to enrich",
        key="article_url"
    )

    # App context for styling
    video_app = st.selectbox(
        "App Context *",
        ["relocation", "placement", "newsroom"],
        index=0,
        help="Which app is this article from? (determines video style)",
        key="video_app"
    )

    # Video model (fixed to seedance-1-pro-fast)
    st.text_input(
        "Video Model",
        value="seedance-1-pro-fast",
        disabled=True,
        help="Using Replicate's seedance-1-pro-fast for 12-second videos"
    )
    video_model = "seedance-1-pro-fast"

    # Video resolution
    video_resolution = st.selectbox(
        "Video Resolution",
        ["480p", "720p"],
        index=0,
        help="480p: Faster generation | 720p: Higher quality"
    )

    # Options
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        min_sections = st.number_input(
            "Minimum Video Sections",
            min_value=1,
            max_value=4,
            value=4,
            help="Ensure at least this many sections have videos"
        )

    with col2:
        force_regenerate = st.checkbox(
            "Force Video Regeneration",
            value=False,
            help="Regenerate video even if article already has one"
        )

    # Submit button
    st.divider()

    if st.button("🎬 Enrich with Videos", type="primary", use_container_width=True, key="enrich_video"):
        # Validation
        if not article_url:
            st.error("❌ Please provide an article URL or slug")
        else:
            # Extract slug from URL if full URL provided
            if "http" in article_url:
                slug = article_url.rstrip('/').split('/')[-1]
            else:
                slug = article_url.strip()

            # Show progress
            with st.spinner("🎬 Enriching article with videos... This takes 2-5 minutes"):
                try:
                    # Call Gateway API
                    response = requests.post(
                        f"{GATEWAY_URL}/v1/workflows/video-enrichment",
                        headers={
                            "Content-Type": "application/json",
                            "X-API-Key": API_KEY
                        },
                        json={
                            "slug": slug,
                            "app": video_app,
                            "video_model": video_model,
                            "video_resolution": video_resolution,
                            "min_sections": min_sections,
                            "force_regenerate": force_regenerate
                        },
                        timeout=30
                    )

                    # Handle response
                    if response.status_code == 200 or response.status_code == 201:
                        data = response.json()

                        # Success message
                        st.success("✅ **Video Enrichment Started!**")

                        # Workflow details
                        st.info(f"**Workflow ID:**\n```\n{data['workflow_id']}\n```")

                        if "article_title" in data:
                            st.info(f"**Article:** {data['article_title']}")

                        st.info(f"**Status:** {data.get('status', 'started').upper()}")

                        # Temporal link
                        temporal_url = f"https://cloud.temporal.io/namespaces/quickstart-quest.zivkb/workflows/{data['workflow_id']}"
                        st.markdown(f"### [📊 Monitor in Temporal UI]({temporal_url})")

                        # Instructions
                        st.divider()
                        st.markdown("""
                        **Next Steps:**
                        1. Click the Temporal link above to monitor progress
                        2. Workflow takes 2-5 minutes to complete
                        3. Videos will be generated and inserted into the article
                        4. Check your article for the new hero video and section videos
                        """)

                    else:
                        # Error response
                        st.error(f"❌ **Error {response.status_code}**")

                        try:
                            error_data = response.json()
                            st.code(error_data, language="json")
                        except:
                            st.text(response.text)

                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. The workflow may still have started - check Temporal UI.")

                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Could not connect to Gateway at {GATEWAY_URL}")
                    st.info("Check that the Gateway URL is correct and the service is running.")

                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
                    st.code(str(e), language="text")

# ===== NEW WORKER TEST TAB =====
with tab_new_worker:
    st.subheader("🧪 New Worker Test")
    st.markdown("*Test the new Python content-worker (quest-py) on separate queue*")

    st.info("""
    **About New Worker:**
    - Uses `new-content-queue` (separate from old workers)
    - Pydantic AI Gateway for all AI calls
    - Clean Python codebase in `quest-py` repo
    - Testing before replacing old workers
    """)

    # Temporal connection settings
    TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "europe-west3.gcp.api.temporal.io:7233")
    TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "quickstart-quest.zivkb")
    TEMPORAL_API_KEY = os.getenv("TEMPORAL_API_KEY", "")

    # Sub-tabs for different workflow types
    nw_tab1, nw_tab2, nw_tab3, nw_tab4 = st.tabs(["🏢 Company", "📝 Article", "🎬 Video", "📰 News"])

    # ===== NEW WORKER: COMPANY =====
    with nw_tab1:
        st.markdown("### Create Company (New Worker)")

        nw_company_url = st.text_input(
            "Company Website URL *",
            placeholder="https://stripe.com",
            help="The company's official website",
            key="nw_company_url"
        )

        nw_company_category = st.selectbox(
            "Category",
            ["AI", "FinTech", "SaaS", "Marketplace", "Investment Bank", "Consulting", "Other"],
            key="nw_company_category"
        )

        nw_company_app = st.selectbox(
            "App Context",
            ["placement", "relocation", "gtm"],
            key="nw_company_app"
        )

        nw_company_jurisdiction = st.selectbox(
            "Jurisdiction",
            ["US", "UK", "EU"],
            key="nw_company_jurisdiction"
        )

        if st.button("🚀 Create Company (New Worker)", type="primary", key="nw_create_company"):
            if not nw_company_url:
                st.error("Please provide a company URL")
            elif not TEMPORAL_API_KEY:
                st.error("TEMPORAL_API_KEY not configured in environment")
            else:
                with st.spinner("Starting workflow on new-content-queue..."):
                    try:
                        from temporalio.client import Client, TLSConfig
                        import uuid

                        async def start_company_workflow():
                            client = await Client.connect(
                                target_host=TEMPORAL_ADDRESS,
                                namespace=TEMPORAL_NAMESPACE,
                                tls=TLSConfig(),
                                api_key=TEMPORAL_API_KEY
                            )

                            workflow_id = f"nw-company-{uuid.uuid4().hex[:8]}"

                            handle = await client.start_workflow(
                                "CreateCompanyWorkflow",
                                {
                                    "url": nw_company_url,
                                    "category": nw_company_category,
                                    "app": nw_company_app,
                                    "jurisdiction": nw_company_jurisdiction,
                                },
                                id=workflow_id,
                                task_queue="new-content-queue",
                            )
                            return workflow_id

                        workflow_id = asyncio.run(start_company_workflow())

                        st.success("✅ **Workflow Started on New Worker!**")
                        st.info(f"**Workflow ID:** `{workflow_id}`")
                        st.info(f"**Queue:** `new-content-queue`")

                        temporal_url = f"https://cloud.temporal.io/namespaces/{TEMPORAL_NAMESPACE}/workflows/{workflow_id}"
                        st.markdown(f"### [📊 Monitor in Temporal UI]({temporal_url})")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # ===== NEW WORKER: ARTICLE =====
    with nw_tab2:
        st.markdown("### Create Article (New Worker)")
        st.warning("⚠️ Article workflow not yet implemented in new worker")

        nw_article_topic = st.text_input(
            "Article Topic *",
            placeholder="OpenAI announces GPT-5 release",
            key="nw_article_topic"
        )

        nw_article_type = st.selectbox(
            "Article Type",
            ["news", "guide", "comparison"],
            key="nw_article_type"
        )

        nw_article_app = st.selectbox(
            "App Context",
            ["placement", "relocation", "gtm"],
            key="nw_article_app"
        )

        if st.button("📝 Create Article (New Worker)", type="primary", key="nw_create_article", disabled=True):
            st.info("Coming soon...")

    # ===== NEW WORKER: VIDEO =====
    with nw_tab3:
        st.markdown("### Generate Video (New Worker)")
        st.warning("⚠️ Video workflow not yet implemented in new worker")

        nw_video_slug = st.text_input(
            "Article Slug *",
            placeholder="openai-gpt5-announcement",
            key="nw_video_slug"
        )

        if st.button("🎬 Generate Video (New Worker)", type="primary", key="nw_create_video", disabled=True):
            st.info("Coming soon...")

    # ===== NEW WORKER: NEWS =====
    with nw_tab4:
        st.markdown("### Monitor News (New Worker)")
        st.warning("⚠️ News monitoring workflow not yet implemented in new worker")

        nw_news_app = st.selectbox(
            "App Context",
            ["placement", "relocation"],
            key="nw_news_app"
        )

        if st.button("📰 Start News Monitor (New Worker)", type="primary", key="nw_start_news", disabled=True):
            st.info("Coming soon...")

# Footer
st.divider()
st.caption("💡 **Tip:** You can track workflow status in the Temporal UI at any time")
