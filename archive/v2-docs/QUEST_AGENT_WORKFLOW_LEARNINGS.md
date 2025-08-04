# Quest Core Agent Workflow Learnings

*Last Updated: December 2024*

## Overview

This document captures key learnings from AI Labs' HIVE coding methodology and Rob Shocks' development patterns, showing how specialized AI agents can dramatically improve Quest Core V2's development velocity and quality.

## The Power of Specialized Agents

### Agent Workflow Architecture (AI Labs)

The HIVE methodology demonstrates a powerful sequential workflow:

```
1. UX Researcher (7 min, 53k tokens)
   ↓
2. Sprint Prioritizer
   ↓
3. UI Designer
   ↓
4. Whimsy Injector (adds micro-interactions)
   ↓
5. Rapid Prototyper
   ↓
6. Frontend Developer (18 min, 130k tokens)
   ↓
7. Test Runner
   ↓
8. Performance Benchmarker
```

**Key Advantages:**
- Each agent gets its own 200k token context window
- Agents can work in parallel
- Context is preserved via .md files
- Specialized expertise for each domain

### The Whimsy Injector - Quest's Secret Weapon

From the contains-studio-agents repository, the whimsy-injector is marked as **PROACTIVE** and specializes in:

- **Micro-interactions**: Smooth animations that delight users
- **Shareable moments**: TikTok-worthy visual experiences
- **Emotional design**: Turning functional UI into joyful experiences
- **First impressions**: Making onboarding memorable

**Perfect for Quest Core:**
- Trinity creation ceremony animations
- Professional Mirror "shock and awe" reveals
- Voice coach visual feedback
- Quest achievement celebrations

### Rob Shocks' Workflow Optimizations

From his Claude Code tutorial, key patterns that apply to Quest:

1. **Parallel Agents**: Run multiple agents simultaneously
   - UI design while backend develops
   - Testing while documentation writes

2. **Custom Slash Commands**: Create reusable patterns
   - `/trinity-mode` - Focus on Trinity logic
   - `/voice-mode` - Hume AI integration focus
   - `/design-mode` - UI without backend

3. **Hooks for Automation**:
   - Audio notifications when tasks complete
   - Pre-commit test runs
   - Automatic context clearing

4. **Feature Branches**: Safe experimentation
   - Each agent works on its own branch
   - Merge when validated
   - Easy rollback if needed

## Quest Core-Specific Agent Workflow

### Proposed Agent Team for Quest V2

1. **Trinity Architect Agent**
   - Designs Trinity creation flows
   - Ensures philosophical alignment
   - Creates emotional journey maps

2. **Voice Coach Specialist**
   - Optimizes Hume AI prompts
   - Designs conversation flows
   - Handles voice interaction edge cases

3. **Quest Matcher Agent**
   - Implements PG Vector for semantic search
   - Creates Trinity-to-job matching algorithms
   - Optimizes recommendation quality

4. **Professional Mirror Designer**
   - Creates "shock and awe" visualizations
   - Implements data transformations
   - Designs shareable moments

5. **Whimsy Injector** (from contains-studio)
   - Adds delightful micro-interactions
   - Creates viral-worthy moments
   - Ensures emotional engagement

### 6-Day Sprint Integration

**Day 1-2: Discovery & Design**
- UX Researcher analyzes user needs
- Trinity Architect designs flows
- UI Designer creates interfaces

**Day 3-4: Implementation**
- Rapid Prototyper builds foundation
- Frontend Developer implements
- Voice Coach Specialist integrates Hume

**Day 5: Polish & Test**
- Whimsy Injector adds delight
- Test Runner validates
- Performance Benchmarker optimizes

**Day 6: Ship & Celebrate**
- Project Shipper coordinates launch
- Analytics Reporter tracks metrics

## Technical Insights

### PG Vector Implementation (from Rob Shocks)

Rob mentions using PG Vector with Neon for semantic search:

```sql
-- Enable vector extension
CREATE EXTENSION vector;

-- Store Trinity embeddings
CREATE TABLE trinity_embeddings (
  user_id UUID,
  quest_vector vector(768),
  service_vector vector(768),
  pledge_vector vector(768)
);

-- Match jobs to Trinity
SELECT job_id, 
  1 - (job_vector <=> trinity_vector) as similarity
FROM job_embeddings
ORDER BY similarity DESC;
```

### Context Management Between Agents

AI Labs shows context saved in .md files:

```
/project
  /docs
    /agent-context
      ux-research.md
      ui-design.md
      implementation-plan.md
      test-results.md
```

### GitIngest for Codebase Understanding

- Converts entire repositories to LLM-readable format
- Enables quick analysis of competitor apps
- Useful for understanding new libraries

## Key Learnings Applied to Quest Core

1. **Specialization Beats Generalization**
   - Purpose-built agents outperform general ones
   - Each agent maintains deep context in its domain

2. **Planning Prevents Problems**
   - Thorough UX research before coding
   - Sprint planning before implementation
   - Design before development

3. **Delight Differentiates**
   - Whimsy Injector proves micro-interactions matter
   - Shareable moments drive viral growth
   - Polish separates good from great

4. **Parallel Processing Accelerates**
   - Multiple agents working simultaneously
   - Context preserved between handoffs
   - 6-day sprints become achievable

## Implementation Recommendations

1. **Immediate Actions**
   - Set up agent directory structure
   - Create Quest-specific agents
   - Implement PG Vector for Trinity matching

2. **Next Sprint**
   - Integrate whimsy-injector
   - Create agent workflow templates
   - Set up parallel agent execution

3. **Future Enhancements**
   - Build Quest-specific agent library
   - Create agent performance metrics
   - Develop agent orchestration system

## Resources

- Contains Studio Agents: https://github.com/contains-studio/agents
- GitIngest: https://gitingest.com
- Rob Shocks' Neon + PG Vector tutorial
- AI Labs HIVE methodology video

---

*"The best apps aren't just built—they're orchestrated by specialized agents working in harmony."*