# Phase 2: Trinity & Quest Implementation

## Overview
Build the core Quest functionality where users earn their Quest through story.

## Priority Order

### 1. Trinity Save Functionality (Week 1)
- [ ] Create `/api/trinity` endpoint
- [ ] Validate all 9 fields (Past/Present/Future × Quest/Service/Pledge)
- [ ] Calculate Trinity clarity score
- [ ] Store in database with proper relationships

### 2. Quest Readiness Gate (Week 1)
- [ ] Implement readiness calculation algorithm
- [ ] 30% qualification threshold
- [ ] Factors: Trinity clarity, story depth, future orientation
- [ ] Create `/api/quest/readiness` endpoint

### 3. Quest Page & Generation (Week 2)
- [ ] Build Quest display page
- [ ] Quest statement generation from Trinity
- [ ] Service and Pledge alignment
- [ ] Visual Quest representation

### 4. AI Coaching Integration (Week 2)
- [ ] OpenRouter setup with model routing
- [ ] Story Coach implementation
- [ ] Quest Coach implementation
- [ ] Coaching session tracking

### 5. Entity Extraction (Week 3)
- [ ] Parse LinkedIn data for skills
- [ ] Extract company entities
- [ ] Create validation workflow
- [ ] Build entity management UI

### 6. Voice Coaching (Week 3-4)
- [ ] Hume AI integration
- [ ] Voice session handling
- [ ] Emotion tracking
- [ ] Session recording

## Technical Requirements

### API Endpoints Needed
```
POST /api/trinity - Save Trinity data
GET  /api/trinity - Retrieve user's Trinity
POST /api/quest/readiness - Check Quest eligibility
POST /api/quest/generate - Generate Quest from Trinity
POST /api/coaching/session - Start coaching session
POST /api/entities/extract - Extract entities from data
```

### Database Updates
- Trinity clarity score tracking
- Quest readiness metrics
- Coaching session records
- Entity validation states

### UI Components
- Trinity form validation
- Quest readiness progress bar
- Quest visualization
- Coaching chat interface
- Entity management dashboard

## Success Metrics
- Trinity completion rate > 80%
- Quest qualification rate ~30%
- Coaching engagement > 10 min/session
- Entity accuracy > 90%

## Dependencies
- OpenRouter API key configured
- Hume AI access granted
- Entity validation logic defined
- Quest visual design approved