# Company Profile Creator Dashboard

Streamlit dashboard for creating company profiles via Temporal workflows.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```bash
GATEWAY_URL=https://quest-gateway-production.up.railway.app
API_KEY=  # Leave blank for dev mode (no auth)
```

3. Run dashboard:
```bash
streamlit run dashboard.py
```

4. Open browser at: http://localhost:8501

## Usage

1. Enter company website URL
2. Select app context and category
3. Configure options (images, publish, rescrape)
4. Click "Create Company Profile"
5. Monitor progress in Temporal UI

## Features

- ✅ Clean form interface
- ✅ Input validation
- ✅ Real-time workflow tracking
- ✅ Direct Temporal UI links
- ✅ Error handling
- ✅ No API key confusion (from .env)

## Notes

- Dashboard runs locally (secure)
- No deployment needed (unless you want to)
- Zero changes to company-worker code
- Gateway endpoints unchanged

## Example

```bash
# Navigate to company-worker directory
cd /Users/dankeegan/quest/company-worker

# Run the dashboard
streamlit run dashboard.py

# Opens browser at http://localhost:8501
# Fill in the form and click "Create Company Profile"
# Monitor progress in the Temporal UI link provided
```

## What the Dashboard Does

1. **Loads Configuration**: Reads `GATEWAY_URL` and `API_KEY` from `.env` file
2. **Displays Form**: Shows a user-friendly form for company creation
3. **Validates Input**: Ensures URL is properly formatted
4. **Calls Gateway API**: Sends POST request to `/v1/workflows/company-creation`
5. **Shows Results**: Displays workflow ID and Temporal UI link
6. **Handles Errors**: Catches and displays any errors gracefully

## Benefits

✅ **No more terminal confusion** - Click buttons instead of curl
✅ **No API key confusion** - Loaded from .env automatically
✅ **No JSON syntax errors** - Form handles it
✅ **Immediate Temporal links** - One click to monitor
✅ **Input validation** - Catches errors before sending
✅ **Zero deployment** - Runs on your laptop
✅ **100% safe** - No code changes to company-worker

## Troubleshooting

### Dashboard won't start
- Check that Streamlit is installed: `pip3 show streamlit`
- Try reinstalling: `pip3 install streamlit==1.31.0`

### Can't connect to Gateway
- Verify `GATEWAY_URL` in `.env` file
- Check that Gateway is running on Railway
- Test Gateway directly: `curl https://quest-gateway-production.up.railway.app/health`

### Workflow fails to start
- Check Temporal credentials in `.env`
- Verify company URL is valid and accessible
- Check Gateway logs on Railway for errors
