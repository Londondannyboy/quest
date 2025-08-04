# Apify Integration Attempts Documentation

## Summary of All Attempts

### Context
- **Task ID**: `LpVuK3Zozwuipa5bp` (confirmed working in Apify console)
- **User ID**: `oagG2IEtw87XfSn3x` 
- **Actor**: `harvestapi/linkedin-profile-scraper`
- **Input Format**: `{ "queries": ["url"], "urls": ["url"] }`

### Attempt 1: Direct API with Actor Name
- **Endpoint**: `/v2/actors/harvestapi/linkedin-profile-scraper/runs`
- **Result**: 404 - Actor not found
- **Issue**: Wrong endpoint format

### Attempt 2: Direct API with Infrastructure Quest Prefix
- **Endpoint**: `/v2/actors/infrastructure_quest/linkedin-profile-scraper/runs`
- **Result**: 404 - Actor not found
- **Issue**: Incorrect actor naming

### Attempt 3: Direct API with Task ID as Actor
- **Endpoint**: `/v2/actors/LpVuK3Zozwuipa5bp/runs`
- **Result**: 404 - Treating task ID as actor name

### Attempt 4: Actor Tasks Endpoint
- **Endpoint**: `/v2/actor-tasks/LpVuK3Zozwuipa5bp/runs`
- **Result**: Failed (details unclear)
- **Issue**: Possibly missing user context

### Attempt 5: User-Specific Task Endpoint
- **Endpoint**: `/v2/users/oagG2IEtw87XfSn3x/actor-tasks/LpVuK3Zozwuipa5bp/runs`
- **Result**: Failed
- **Issue**: Wrong endpoint structure

### Attempt 6: MCP Integration v1
- **Method**: Using @modelcontextprotocol/sdk with complex setup
- **Result**: JSON-RPC protocol errors
- **Issues**: 
  - Overcomplicated implementation
  - Protocol validation failures
  - Wrong header requirements

### Attempt 7: MCP Integration v2 (Simplified)
- **Method**: Direct HTTP calls to https://mcp.apify.com
- **Result**: Not fully tested due to continued Direct API failures
- **Issues**: 
  - Unclear how to properly authenticate
  - Documentation shows OAuth flow primarily

## Environment Variables Confusion
- Started with `APIFY_API_KEY`
- MCP docs suggest `APIFY_TOKEN`
- Added both for compatibility
- Unclear which is correct for which method

## Key Observations
1. **Working in Apify Console**: The task runs successfully when triggered from the Apify console
2. **API Authentication Works**: We can connect to Apify API (test connection succeeds)
3. **Endpoint Format Issue**: The main problem seems to be the exact endpoint format
4. **MCP vs Direct API**: Unclear which approach is better for programmatic access

## What We Know Works
- Task ID: `LpVuK3Zozwuipa5bp`
- User ID: `oagG2IEtw87XfSn3x`
- Input format: `{ "queries": ["url"], "urls": ["url"] }`
- Authentication: API key is valid

## What We Don't Know
- Exact endpoint format for user-created tasks
- Whether task endpoint needs user context
- Difference between APIFY_API_KEY and APIFY_TOKEN
- How to properly use MCP server for task execution

## Recommended Next Steps
1. Create minimal test project with ONLY Apify integration
2. Test both MCP and Direct API in isolation
3. Use exact same credentials and task ID
4. Once working, port solution back to main project

## Failed Code Patterns to Avoid
```javascript
// DON'T: User-specific endpoints
`/v2/users/${userId}/actor-tasks/${taskId}/runs`

// DON'T: Actor name with task ID
`/v2/actors/${taskId}/runs`

// DON'T: Complex MCP setup with SDK transports
new StdioClientTransport({ command: "npx", ... })
```

## Questions for Minimal Test
1. Can we run the task with just task ID?
2. Do we need user context in the endpoint?
3. Is MCP actually simpler than Direct API?
4. What's the exact working endpoint format?