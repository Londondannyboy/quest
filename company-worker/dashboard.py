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
    page_title="Company Profile Creator",
    page_icon="🏢",
    layout="centered"
)

# Header
st.title("🏢 Company Profile Creator")
st.markdown("*AI-powered company profile generation*")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    st.text(f"Gateway: {GATEWAY_URL.split('//')[1][:30]}...")
    if API_KEY:
        st.success("✅ API Key configured")
    else:
        st.warning("⚠️ Set API_KEY in .env file")

    st.divider()
    st.caption("Powered by Temporal + Claude Sonnet")

# Main form
st.subheader("Create Company Profile")

# Company URL (required)
url = st.text_input(
    "Company Website URL *",
    placeholder="https://acme.com",
    help="The company's official website"
)

# App selection
app = st.selectbox(
    "App Context *",
    ["placement", "relocation", "chief-of-staff", "gtm", "newsroom"],
    index=0,
    help="Which app is this profile for?"
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
jurisdiction = st.selectbox(
    "Jurisdiction *",
    ["UK", "US", "EU", "SG", "AU", "CA", "HK", "AE"],
    index=0,
    help="Geographic focus for research"
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

if st.button("✨ Create Company Profile", type="primary", use_container_width=True):
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
                        "jurisdiction": jurisdiction,
                        "app": app,
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

# Footer
st.divider()
st.caption("💡 **Tip:** You can track workflow status in the Temporal UI at any time")
