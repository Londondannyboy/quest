# Sanity MCP Setup Guide for SEO Pages

## Prerequisites

1. **Sanity Project Setup**
   - You need a Sanity project ID
   - You need a dataset (e.g., "production")
   - You have the API token in environment variable `sanity_api_key`

2. **Deploy Your Schema**
   First, add the schema to your Sanity Studio and deploy it:
   ```bash
   # In your Sanity studio directory
   npx sanity schema deploy
   ```

## Claude Desktop Configuration

Add this configuration to your Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "sanity": {
      "command": "npx",
      "args": ["-y", "@sanity/mcp-server@latest"],
      "env": {
        "SANITY_PROJECT_ID": "your-project-id-here",
        "SANITY_DATASET": "production",
        "SANITY_API_TOKEN": "${sanity_api_key}",
        "MCP_USER_ROLE": "developer"
      }
    }
  }
}
```

**Note**: Replace `your-project-id-here` with your actual Sanity project ID.

## Using the MCP in Claude Desktop

Once configured, you can use Claude Desktop to:

1. **Initialize the connection**:
   ```
   Use the get_initial_context tool first
   ```

2. **Create the home page**:
   ```
   Create a home page with type "home" using create_document tool
   Include news items and optimize for the keyword "private equity news"
   ```

3. **Create placement agent pages**:
   ```
   Create 10 placement agent pages for locations:
   - London, UK
   - Paris, France
   - Frankfurt, Germany
   - Zurich, Switzerland
   - New York, USA
   - Hong Kong
   - Singapore
   - Dubai, UAE
   - Tokyo, Japan
   - Sydney, Australia
   ```

## Example Commands for Claude Desktop

Here's what you would tell Claude in the Desktop app:

```
First, call get_initial_context to initialize the connection.

Then create a home page:
- Page type: home
- Title: "Private Equity News and Insights"
- Keyword: "private equity news"
- Include 5 recent news items
- Ensure keyword appears 5 times in content
- Include keyword in H1, H2 tags
- Bold the keyword at least once
- Add hero image with keyword in alt text

Next, create 10 placement agent pages:
For each location (London, Paris, Frankfurt, etc.):
- Page type: placement-agent
- Title: "Private Equity Placement Agents [Location]"
- Keyword: "private equity placement agents [location]"
- Create comprehensive content about placement agents in that location
- Include keyword 5 times naturally in content
- Add keyword to H1 and all H2 headings
- Bold keyword at least once
- Add 2-3 images with keyword in alt text
- Link to other placement agent pages

Finally, update all pages to include internal links to each other.
```

## Manual Approach (Without MCP)

If you prefer to create content programmatically without MCP, see the `content-generation-script.js` file.