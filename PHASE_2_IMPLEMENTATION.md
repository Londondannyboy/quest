# Phase 2 Implementation: Trinity & Quest Journey

**Start Date**: January 28, 2025  
**Target Completion**: February 18, 2025  
**Philosophy**: Coach-guided Trinity discovery through authentic story exploration

---

## 🎯 Implementation Strategy

### Core Decision: Coach-Guided Trinity Discovery

Users will NOT be prompted for Trinity immediately. Instead:

1. Professional Mirror presents their "instant twin"
2. Story Coach explores their journey
3. Quest Coach reveals patterns and guides Trinity discovery
4. Delivery Coach gates Quest readiness (30% pass rate)

---

## 📅 Week 1: Core Trinity Infrastructure (Jan 28 - Feb 3)

### Trinity Save Functionality ✅

- [x] Create `/api/trinity` POST endpoint
  - [x] Accept all 9 fields (Past/Present/Future × Quest/Service/Pledge)
  - [x] Validate non-empty, meaningful responses (min 10 words)
  - [x] Calculate Trinity clarity score
  - [x] Store with proper entity relationships
- [x] Create `/api/trinity` GET endpoint
  - [x] Retrieve user's Trinity data
  - [x] Include clarity score and timestamps
  - [x] Return coaching context if available

### Quest Readiness Gate ✅

- [x] Implement readiness calculation algorithm
  ```typescript
  const readinessScore =
    storyDepth * 0.3 + // Professional Mirror completeness
    trinityClarity * 0.4 + // Trinity response quality
    futureOrientation * 0.3 // Forward-looking elements
  ```
- [x] Create `/api/quest/readiness` endpoint
  - [x] Calculate score based on user data
  - [x] Return: QUEST_READY (70%+), PREPARING (40-69%), NOT_YET (<40%)
  - [x] Include coaching recommendations
- [x] Ensure ~30% qualification rate through scoring calibration

### Coach Integration in Trinity Flow

- [ ] Update Trinity page UI for coach guidance
  - [ ] Add coach message display area
  - [ ] Implement real-time coach suggestions
  - [ ] Create field-by-field guidance
- [ ] Add coach personality switching
  - [ ] Story Coach → Quest Coach transition
  - [ ] Signature sound effects
  - [ ] Visual transition animations
- [ ] Track coaching session state
  - [ ] Current coach type
  - [ ] Messages exchanged
  - [ ] Trinity completion progress

---

## 📅 Week 2: AI Coaching & Quest Generation (Feb 4-10)

### OpenRouter Integration

- [ ] Configure OpenRouter API
  - [ ] Set up API key and base URL
  - [ ] Implement model routing logic
  - [ ] Add fallback handling
- [ ] Implement Story Coach
  - [ ] Warm, empathetic personality
  - [ ] Professional Mirror exploration prompts
  - [ ] Transition detection logic
- [ ] Implement Quest Coach
  - [ ] Pattern recognition prompts
  - [ ] Trinity guidance system
  - [ ] Evolution highlighting
- [ ] Implement Delivery Coach
  - [ ] Firm assessment personality
  - [ ] Quest readiness evaluation
  - [ ] Commitment verification

### Quest Page & Generation

- [ ] Create `/app/quest/[userId]/page.tsx`
  - [ ] Display generated Quest statement
  - [ ] Show Trinity evolution visual
  - [ ] Include Service and Pledge
- [ ] Build Quest generation logic
  - [ ] Transform Trinity into Quest statement
  - [ ] Create compelling narrative
  - [ ] Ensure uniqueness and authenticity
- [ ] Implement Quest activation flow
  - [ ] Confirmation ceremony
  - [ ] Public/private toggle
  - [ ] Share functionality

---

## 📅 Week 3-4: Advanced Features (Feb 11-18)

### Entity Extraction

- [ ] Create entity parsing service
  - [ ] Extract companies from Professional Mirror
  - [ ] Identify skills and competencies
  - [ ] Find education institutions
- [ ] Build synthetic entity system
  - [ ] Provisional entity creation
  - [ ] Confidence scoring
  - [ ] User validation workflow
- [ ] Create entity management UI
  - [ ] Entity browser/search
  - [ ] Validation interface
  - [ ] Relationship mapping

### Voice Coaching (Hume AI)

- [ ] Integrate Hume AI EVI 3
  - [ ] WebSocket connection handling
  - [ ] Voice session management
  - [ ] Emotion tracking integration
- [ ] Implement voice Trinity input
  - [ ] Speech-to-text for Trinity fields
  - [ ] Voice coach conversations
  - [ ] Session recording/playback
- [ ] Create voice UI components
  - [ ] Voice activation button
  - [ ] Audio visualizer
  - [ ] Emotion display

---

## 🎯 Success Metrics

### Quantitative

- Trinity completion rate > 80%
- Quest qualification rate ~30%
- Average coaching session > 10 minutes
- Trinity clarity score > 70% for qualified users
- Entity extraction accuracy > 90%

### Qualitative

- Users report feeling "seen" by Professional Mirror
- Trinity feels "discovered" not "assigned"
- Quest statements inspire action
- Coaching conversations feel natural

---

## 🚧 Current Blockers

### Environment Variables Needed

- [ ] OpenRouter API key
- [ ] Hume AI credentials
- [ ] Neon database URLs

### Design Decisions Pending

- [ ] Trinity visual representation
- [ ] Quest page layout
- [ ] Coach avatar designs
- [ ] Transition sound effects

---

## 📝 Daily Progress Log

### January 28, 2025

- Created Phase 2 implementation plan
- Defined coach-guided Trinity discovery approach
- Set up detailed todo list for Week 1
- ✅ Implemented Trinity save/retrieve endpoints with clarity scoring
- ✅ Built Quest readiness gate with 30% threshold algorithm
- ✅ Created comprehensive validation and recommendations system

---

## 🔗 Related Documents

- [V2_PRODUCT_REQUIREMENTS.md](./V2_PRODUCT_REQUIREMENTS.md) - Full product spec
- [PHASE_2_PLAN.md](./PHASE_2_PLAN.md) - Original phase plan
- [TRINITY_COACHING_FLOW.md](./TRINITY_COACHING_FLOW.md) - User journey details (to be created)
