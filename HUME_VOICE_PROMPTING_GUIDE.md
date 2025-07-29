# Hume AI Voice Prompting Guide for Quest Core V2

This guide documents best practices for creating and managing voice prompts for the Quest Core V2 coaching system, based on Hume AI's EVI 3 prompting guidelines.

## Overview

Quest Core V2 uses three distinct AI coaches, each with unique personalities and coaching styles:

- **Story Coach** - Warm, empathetic biographer
- **Quest Coach** - Energetic pattern seeker
- **Delivery Coach** - Firm, action-oriented guide

## Admin Interface

Access the coach prompt management system at `/admin/coaches` (requires admin privileges).

## Voice Prompt Structure

Each coach prompt should include these components:

### 1. Role Description

Define the coach's identity and purpose in 1-2 sentences.

```
Example: "A warm, empathetic Story Coach (biographer) who helps users discover their authentic professional story through deep listening and thoughtful questions."
```

### 2. Personality & Tone

Specify how the coach should sound and feel.

```
Example: "Warm, patient, and genuinely curious. Speaks with a gentle but purposeful tone, like a wise mentor who truly cares about understanding their story."
```

### 3. Conversation Guidelines

Bullet-pointed behavioral instructions:

- Ask open-ended questions
- Listen actively and reflect back
- Use minimal encouragers
- Allow for pauses and silence
- Focus on specific coaching goals

### 4. Example Interactions

Provide 2-3 few-shot examples showing ideal responses:

```
User: "I left my corporate job to start my own company."
Coach: "Oh wow, that must have been a big decision. What was happening in your life that led you to take that leap?"
```

### 5. Backchanneling & Encouragers

Specify the coach's listening signals:

- Story Coach: "I see", "Yes", "That makes sense", "I hear you"
- Quest Coach: "Yes!", "Exactly!", "That's it!", "Keep going!"
- Delivery Coach: "Good", "Right", "And?", "Be specific"

### 6. Emotional Response Guidelines

How the coach should adapt to user emotions:

- Match emotional energy appropriately
- Show empathy for struggles
- Celebrate breakthroughs
- Maintain coach-specific energy levels

### 7. Voice Characteristics

Technical guidance for vocal delivery:

- Speaking pace (slow/moderate/fast)
- Pitch variations
- Use of pauses
- Emphasis patterns

## Best Practices from Hume AI

### Design for Spoken Output

- Avoid text formatting (bullets, numbers) in actual responses
- Use natural discourse markers ("oh", "well", "you know")
- Include vocal inflections and natural speech patterns

### Optimal Prompt Length

- Keep prompts between 2000-5000 tokens
- Focus on quality over quantity
- Use clear, structured sections

### Conversation Flow

- Implement natural turn-taking
- Don't interrupt users
- Allow for pauses and silence
- Use backchanneling to show active listening

### Emotional Intelligence

- Respond appropriately to detected emotions
- Adjust tone based on user state
- Maintain coach personality while being responsive

## Coach-Specific Guidelines

### Story Coach

**Goal**: Help users explore their professional journey

- Ask about transitions and motivations
- Notice patterns without judging
- Create psychological safety
- Focus on the "why" behind decisions

### Quest Coach

**Goal**: Reveal Trinity patterns and potential

- Connect dots across timeline
- Build excitement about possibilities
- Use pattern-revealing language
- Help them dream bigger

### Delivery Coach

**Goal**: Turn insights into concrete action

- Push for specific commitments
- Challenge vague responses
- Create urgency around action
- Maintain high standards (only 30% Quest-ready)

## Testing Your Prompts

1. **Conversation Quality**
   - Does the coach maintain their personality?
   - Are responses natural and conversational?
   - Is the emotional tone appropriate?

2. **Goal Achievement**
   - Story Coach: Are users opening up about their journey?
   - Quest Coach: Are patterns being revealed?
   - Delivery Coach: Are concrete commitments made?

3. **Voice Quality**
   - Does the voice match the coach personality?
   - Are pauses and emphasis used effectively?
   - Is the pacing appropriate?

## Integration with Hume Configuration

The prompts are integrated through:

1. Hume Dashboard Configuration (ID: 671d99bc-1358-4aa7-b92a-d6b762cb18b5)
2. CLM Endpoint: `/api/hume-clm-sse/chat/completions`
3. Voice Selection: Currently using "Inspired Man" voice

## Updating Prompts

1. Navigate to `/admin/coaches`
2. Select the coach to edit
3. Update prompt components
4. Save changes
5. Test in Trinity interface

## Measuring Success

Monitor these metrics:

- User engagement duration
- Trinity clarity scores
- Quest readiness rates
- Emotional response patterns
- Conversation completion rates

## Common Pitfalls to Avoid

1. **Over-scripting**: Keep responses natural, not robotic
2. **Ignoring emotions**: Always respond to detected emotional states
3. **Being too directive**: Let users discover insights
4. **Losing personality**: Maintain consistent coach character
5. **Poor pacing**: Use appropriate pauses and speaking speed

## Resources

- [Hume AI Prompting Guide](https://dev.hume.ai/docs/speech-to-speech-evi/guides/prompting)
- [EVI 3 Documentation](https://dev.hume.ai/docs/speech-to-speech-evi/overview)
- Admin Interface: `/admin/coaches`
- Test Interface: `/trinity`
