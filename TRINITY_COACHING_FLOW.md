# Trinity Coaching Flow: The Journey to Quest

**Philosophy**: Users don't fill out forms - they discover their Trinity through guided conversation.

---

## 🌟 The Complete User Journey

### Entry: "Begin Your Story"

```
User provides LinkedIn URL or name
     ↓
"May we discover your professional story?"
     ↓
Professional Mirror creation begins
```

---

## Act 1: Professional Mirror (The Instant Twin)

**Duration**: 3-5 minutes  
**Coach**: None (UI-driven)  
**Purpose**: Build trust through transparency

### What Happens:

1. **Progressive Discovery**
   - LinkedIn scraping with real-time updates
   - "Finding your experience at [Company]..."
   - "Discovering your education journey..."
   - Additional sources enhance the mirror

2. **Mirror Presentation**
   - Interactive timeline with floating nodes
   - "This is how the world sees you"
   - Click any node to correct/enhance
   - Transparency about what was found

3. **User Actions**
   - Validate or correct information
   - Add missing experiences
   - Provide context for transitions

### Transition Trigger:

Once user confirms mirror accuracy → Story Coach introduction

---

## Act 2: Story Discovery with Story Coach

**Duration**: 5-7 minutes  
**Coach**: Story Coach (Female, Warm)  
**Purpose**: Uncover the WHY behind the WHAT

### Coach Introduction:

> "Hello, I'm your Story Coach. I see your professional journey laid out here - it's impressive. But I'm more interested in what drove these choices. Let's explore your story together."

### Conversation Flow:

1. **Opening Questions**
   - "What drew you to [first career choice]?"
   - "I notice you transitioned from [X] to [Y]. What inspired that change?"
   - "Tell me about a moment when you felt most aligned with your work..."

2. **Deepening Understanding**
   - Coach notices patterns without labeling
   - Asks about emotions and motivations
   - Explores values through stories
   - "What did success mean to you then? And now?"

3. **Pattern Recognition** (Internal)
   - Coach tracks themes across responses
   - Identifies evolution of purpose
   - Prepares handoff to Quest Coach

### Transition Trigger:

When sufficient depth achieved → Quest Coach introduction

---

## Act 3: Trinity Recognition with Quest Coach

**Duration**: 5-7 minutes  
**Coach**: Quest Coach (Male, Energetic)  
**Purpose**: Reveal patterns and guide Trinity articulation

### Coach Transition:

_[Signature sound effect - like a bell or chime]_

> "Welcome! I'm your Quest Coach. I've been listening, and I see something remarkable emerging. Your Story Coach helped you explore your journey - now let's recognize the patterns that define your Trinity."

### Trinity Discovery Process:

1. **Pattern Revelation**

   > "I notice three distinct phases in your evolution..."
   - Coach highlights Past motivations
   - Connects to Present drivers
   - Projects Future aspirations

2. **Trinity Framework Introduction**

   > "In Quest, we call this your Trinity - three elements across time:
   >
   > - Your Quest: What drives you?
   > - Your Service: How do you create value?
   > - Your Pledge: What do you promise?"

3. **Guided Trinity Articulation**
   For each time period (Past/Present/Future):

   **Quest Discovery**:

   > "Looking at your early career, what was the deeper purpose driving you?"
   > [User responds]
   > "I hear [reflection]. Could we capture that as: [suggested Quest]?"

   **Service Discovery**:

   > "How did you uniquely serve others in that role?"
   > [User responds]
   > "So your service was really about [reflection]?"

   **Pledge Discovery**:

   > "What promise did you make to yourself or others?"
   > [User responds]
   > "That commitment to [reflection] really stands out."

4. **Trinity Validation**
   - Coach presents complete Trinity
   - User can refine each element
   - Calculate Trinity clarity score

### Transition Trigger:

Trinity clarity > 60% → Delivery Coach assessment

---

## Act 4: Quest Readiness with Delivery Coach

**Duration**: 3-5 minutes  
**Coach**: Delivery Coach (Direct, Achievement-focused)  
**Purpose**: Gate Quest activation with high standards

### Coach Transition:

_[Signature sound effect - more dramatic, like a gong]_

> "I'm your Delivery Coach. Let's cut to the chase. You've discovered your Trinity, but a Quest isn't just about knowing - it's about doing. Are you ready to make this real?"

### Assessment Process:

1. **Commitment Check**

   > "Your Future Quest states [X]. What's your first concrete step?"
   > "When obstacles arise - and they will - what will keep you going?"
   > "Who will hold you accountable?"

2. **Readiness Evaluation**
   - Checks for specificity
   - Challenges vague answers
   - Pushes for commitment

3. **Three Possible Outcomes**

   **QUEST_READY (30% of users)**:

   > "I see fire in your eyes. You're not just dreaming - you're ready to build. Your Quest awaits activation."
   > → Proceed to Quest creation

   **PREPARING (65% of users)**:

   > "You're close, but not quite there. Your Trinity needs more clarity. Let's work on [specific area]."
   > → Guided exercises to strengthen Trinity

   **NOT_YET (5% of users)**:

   > "I respect your honesty, but you're not ready for a Quest. That's okay. Return when your purpose burns brighter."
   > → Supportive resources and invitation to return

---

## 🎭 Coach Personality Guidelines

### Story Coach

- **Voice**: Warm, patient, curious
- **Focus**: Emotional intelligence, empathy
- **Never**: Rushes or judges
- **Always**: Creates safe space for vulnerability

### Quest Coach

- **Voice**: Energetic, insightful, forward-looking
- **Focus**: Pattern recognition, potential
- **Never**: Tells user who they are
- **Always**: Reveals what's already there

### Delivery Coach

- **Voice**: Direct, challenging, supportive
- **Focus**: Action, commitment, reality
- **Never**: Accepts BS or vagueness
- **Always**: Maintains high standards

---

## 🔄 Session State Management

### Data Tracked:

```typescript
interface CoachingSession {
  userId: string
  currentCoach: 'story' | 'quest' | 'delivery'
  phase: 'mirror' | 'story' | 'trinity' | 'readiness'
  messages: Message[]
  trinityProgress: {
    past: { quest?: string; service?: string; pledge?: string }
    present: { quest?: string; service?: string; pledge?: string }
    future: { quest?: string; service?: string; pledge?: string }
  }
  clarityScore: number
  readinessScore: number
  startTime: Date
  lastActivity: Date
}
```

### State Transitions:

- Save after each coach message
- Allow resume from any point
- Track partial Trinity completion
- Maintain conversation context

---

## 💡 Implementation Notes

1. **No Forms**: Trinity emerges through conversation, not form fields
2. **Natural Language**: Coaches speak conversationally, not robotically
3. **User Agency**: Users can always refine or restart
4. **High Standards**: Only ~30% earn Quest immediately
5. **Encouragement**: Even "not ready" users feel supported

---

## 🎯 Success Indicators

- Users say "That's exactly it!" during Trinity discovery
- Trinity feels discovered, not assigned
- Users thank coaches for insights
- Quest readiness feels earned, not given
- Even rejected users want to return
