# Quick Start Guide: Sanity SEO Pages with MCP

## What We've Created

1. **Sanity Schema** (`sanity-seo-schema.ts`) - Defines the structure for SEO-optimized pages
2. **MCP Setup Guide** (`mcp-setup-guide.md`) - Instructions for using with Claude Desktop
3. **Content Generation Script** (`content-generation-script.js`) - Automated page creation
4. **Internal Linking Guide** (`internal-linking-guide.md`) - SEO linking strategy

## Option 1: Using MCP with Claude Desktop (Recommended)

### Step 1: Setup Sanity Studio
```bash
# Add the schema to your Sanity studio schemas
cp sanity-seo-schema.ts your-studio/schemas/

# Deploy the schema
cd your-studio
npx sanity schema deploy
```

### Step 2: Configure Claude Desktop
Add to your Claude Desktop MCP settings:
```json
{
  "mcpServers": {
    "sanity": {
      "command": "npx",
      "args": ["-y", "@sanity/mcp-server@latest"],
      "env": {
        "SANITY_PROJECT_ID": "your-project-id",
        "SANITY_DATASET": "production",
        "SANITY_API_TOKEN": "${sanity_api_key}",
        "MCP_USER_ROLE": "developer"
      }
    }
  }
}
```

### Step 3: Use Claude Desktop
Tell Claude: "First call get_initial_context, then create SEO-optimized pages for private equity placement agents with proper keyword optimization and internal linking."

## Option 2: Using the Generation Script

### Step 1: Install Dependencies
```bash
npm install @sanity/client
```

### Step 2: Set Environment Variables
```bash
export SANITY_PROJECT_ID="your-project-id"
export SANITY_DATASET="production"
export SANITY_API_TOKEN="your-token"
```

### Step 3: Run the Script
```bash
node content-generation-script.js
```

## SEO Requirements Met ✅

Each page includes:
- ✅ Target keyword repeated 5+ times
- ✅ Keyword in H1 heading
- ✅ Keyword in all H2 headings
- ✅ Keyword in bold at least once
- ✅ Keyword in all image alt texts
- ✅ Internal links to all other pages
- ✅ Meta description with keyword
- ✅ SEO score tracking

## Page Structure Created

1. **Home Page**: Private equity news hub with latest updates
2. **10 Location Pages**:
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

## Next Steps

1. **Add Images**: Upload actual images to Sanity and update the image fields
2. **Customize Content**: Refine the generated content for your specific needs
3. **Frontend Implementation**: Build the frontend to display these pages
4. **Monitor Performance**: Use Google Search Console to track SEO performance

## Troubleshooting

- **Schema not found**: Make sure to run `npx sanity schema deploy`
- **Authentication error**: Verify your API token has write permissions
- **MCP not working**: Check Claude Desktop logs for connection issues

Your SEO-optimized private equity pages are now ready to be created!