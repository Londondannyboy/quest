import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GATEWAY_URL = os.getenv("GATEWAY_URL", "https://quest-gateway-production.up.railway.app")
API_KEY = os.getenv("API_KEY", "")

# Page config
st.set_page_config(
    page_title="Quest Content Creator",
    page_icon="🚀",
    layout="centered"
)

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
tab_company, tab_article = st.tabs(["🏢 Company Profile", "📝 Article Creation"])

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
                        f"{GATEWAY_URL}/v1/workflows/company-worker",
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
            min_value=500,
            max_value=3000,
            value=1500,
            step=100,
            help="Target length of the article"
        )

        num_research_sources = st.slider(
            "Research Sources",
            min_value=3,
            max_value=15,
            value=10,
            step=1,
            help="Number of sources to crawl for research"
        )

    with col2:
        generate_images = st.checkbox(
            "Generate Images",
            value=False,
            help="Generate AI images (adds 5-8 min, ~$0.10)"
        )

        if generate_images:
            st.caption("⏱️ +5-8 minutes for images")
            st.caption("💰 ~$0.10 for 3-5 images")

    # Cost estimate
    st.divider()
    estimated_cost = 0.04 + 0.04 + 0.015  # Serper + Exa + AI
    if generate_images:
        estimated_cost += 0.10

    st.caption(f"💰 **Estimated cost:** ${estimated_cost:.2f}")

    time_estimate = "3-5 minutes"
    if generate_images:
        time_estimate = "8-13 minutes"
    st.caption(f"⏱️ **Estimated time:** {time_estimate}")

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
                        "generate_images": generate_images,
                        "num_research_sources": num_research_sources
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
                        st.markdown(f"""
                        **What's happening:**
                        1. 🔍 Researching topic (Serper + Exa)
                        2. 📥 Crawling discovered URLs (Crawl4AI)
                        3. 🧠 Querying Zep knowledge graph
                        4. ✍️ Generating article content (Gemini 2.5 Flash)
                        {"5. 🎨 Generating images (Flux Kontext)" if generate_images else ""}

                        **Estimated time:** {time_estimate}
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

# Footer
st.divider()
st.caption("💡 **Tip:** You can track workflow status in the Temporal UI at any time")
