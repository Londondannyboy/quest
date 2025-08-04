# Next Session: Apify Integration

## Current Status
LinkedIn scraping is failing despite having a working task in Apify console. We've tried multiple approaches without success.

## Your Working Configuration
- **Task ID**: `LpVuK3Zozwuipa5bp` (100% confirmed working in Apify console)
- **User ID**: `oagG2IEtw87XfSn3x`
- **Actor**: `harvestapi/linkedin-profile-scraper`
- **Console URL**: `https://console.apify.com/actors/tasks/WMsh4V8Vna4SHB4D9/runs/h7Cx7tn8SuQUSxI17#log`
- **Input Format**: 
  ```json
  {
    "queries": ["https://www.linkedin.com/in/dankeegan/"],
    "urls": ["https://www.linkedin.com/in/williamhgates"]
  }
  ```

## Recommended Approach for Next Session

### Step 1: Create Minimal Test Project
```bash
mkdir apify-test
cd apify-test
npm init -y
npm install node-fetch
```

### Step 2: Test Direct API First
Create a simple script that ONLY tests the Apify API:
```javascript
// test-direct-api.js
const API_KEY = 'your_actual_api_key';
const TASK_ID = 'LpVuK3Zozwuipa5bp';

async function testDirectAPI() {
  // Try different endpoint formats
  const endpoints = [
    `https://api.apify.com/v2/actor-tasks/${TASK_ID}/runs`,
    `https://api.apify.com/v2/actor-tasks/oagG2IEtw87XfSn3x~${TASK_ID}/runs`,
    `https://api.apify.com/v2/acts/oagG2IEtw87XfSn3x~${TASK_ID}/runs`
  ];
  
  // Test each endpoint...
}
```

### Step 3: Test MCP Approach
Only if Direct API fails, test MCP:
```bash
npm install @apify/actors-mcp-server
```

### Step 4: What to Focus On
1. **Get the exact endpoint format** - This is the main issue
2. **Test with minimal code** - No frameworks, just fetch
3. **Log everything** - Full request/response details
4. **Try variations** - Different endpoint formats

## Key Questions to Answer
1. What is the EXACT endpoint format for running a user task?
2. Does the endpoint need the user ID?
3. What's the difference between actor-tasks and acts endpoints?
4. Which auth header format works?

## Once It Works
When you get it working in the minimal test:
1. Document the exact working code
2. Note the exact endpoint format
3. Bring that back to quest-core
4. Update the implementation with the working pattern

## Important Notes
- The task DEFINITELY works (proven in console)
- Our API key is valid (test connection works)
- The issue is specifically the endpoint format
- Don't overcomplicate - start with the simplest possible test

Good luck! Once you crack this in isolation, it should be straightforward to fix in the main project.