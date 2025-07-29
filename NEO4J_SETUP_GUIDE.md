# Neo4j Setup Guide for Quest Core V2

## Quick Start with Neo4j Aura Free

1. **Visit**: https://neo4j.com/cloud/aura-free/
2. **Sign up** for a free account
3. **Create Instance**:
   - Click "New Instance"
   - Choose "AuraDB Free"
   - Select your region (choose closest for best performance)
   - Name: "quest-core-network"

4. **Save Credentials** (shown only once!):

   ```bash
   Connection URI: neo4j+s://xxxxxxxx.databases.neo4j.io
   Username: neo4j
   Password: [auto-generated - SAVE THIS!]
   ```

5. **Add to Vercel**:
   - Go to your Vercel project settings
   - Navigate to Environment Variables
   - Add:
     - `NEO4J_URI` = your connection URI
     - `NEO4J_USER` = neo4j
     - `NEO4J_PASSWORD` = your password

6. **Test Connection**:
   - Redeploy your Vercel app
   - Visit `/quest-network` page
   - You should see the 3D network visualization

## What Neo4j Stores for Quest Core

- **User Nodes**: Each Quest user becomes a node
- **Colleague Relationships**: LinkedIn connections
- **Quest Connections**: Similar/complementary Quest alignments
- **Network Metadata**: Companies, titles, clarity scores

## Troubleshooting

### "Connection Failed" Error

- Check if your IP is whitelisted (Aura has IP restrictions)
- Verify credentials are exact (no extra spaces)
- Ensure you're using `neo4j+s://` protocol (with +s for SSL)

### Empty Network

- This is normal for new users
- Network builds as more colleagues join Quest
- Demo data shows if no real connections exist

## Neo4j Browser Access

Once created, you can explore your data:

1. Click "Open with Neo4j Browser" in Aura console
2. Run queries like:
   ```cypher
   MATCH (n) RETURN n LIMIT 25
   ```

## Free Tier Limits

Neo4j Aura Free includes:

- 1 database
- 50K nodes
- 175K relationships
- 4GB storage

More than enough for Quest Core's network visualization!
