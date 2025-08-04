# Quest Core V2 Style Guide

> "Every interaction is sacred. Every pixel has purpose."

---

## 🎯 Philosophy & Principles

### Manifesto Alignment
This style guide embodies Quest Core V2's sacred journey from Story → Trinity → Quest. Every design decision honors our commitment to professional awakening while maintaining technical excellence.

### Core Design Principles
1. **Sacred Simplicity** - Complex journeys presented with elegant clarity
2. **Earned Progression** - Visual weight increases as users prove readiness
3. **Accessible Awakening** - Every seeker can access their Quest, regardless of ability
4. **Living Design** - Interfaces that evolve with user growth
5. **Testable Truth** - Every design decision can be validated programmatically

---

## 🌈 Design Tokens

### Color System

#### Primary Palette
```css
/* Sacred Journey Colors */
--quest-primary: #00D4B8;        /* Aurora Fade - Present/Active */
--quest-past: #4F46E5;           /* Electric Violet - Past/Memory */
--quest-future: #8B5CF6;         /* Purple - Future/Potential */

/* Semantic Colors */
--quest-ready: #10B981;          /* Ready for Quest */
--quest-preparing: #F59E0B;      /* Preparing/Learning */
--quest-not-yet: #94A3B8;        /* Not Yet Ready */

/* Background Hierarchy */
--quest-bg-void: #0A0E1A;        /* Deep space - the unknown */
--quest-bg-mirror: #1A1D29;      /* Professional Mirror surface */
--quest-bg-story: #2A2D3A;       /* Story telling space */
```

#### Color Accessibility
- **Contrast Ratios**: All text meets WCAG 2.1 AA (4.5:1 normal, 3:1 large)
- **Color Independence**: Information never conveyed by color alone
- **Focus Indicators**: 3px outline with 2:1 contrast ratio

### Typography

#### Font Hierarchy
```css
/* Sacred Text Scale */
--quest-text-oracle: 4rem;       /* 64px - Major revelations */
--quest-text-truth: 3rem;        /* 48px - Core truths */
--quest-text-insight: 2.25rem;   /* 36px - Key insights */
--quest-text-wisdom: 1.5rem;     /* 24px - Guidance */
--quest-text-story: 1rem;        /* 16px - Narrative */
--quest-text-whisper: 0.875rem;  /* 14px - Subtle hints */
```

#### Voice & Tone by Coach
- **Biographer**: Warm, curious, patient (font-weight: 400)
- **Pattern Seeker**: Insightful, connecting (font-weight: 500)
- **Quest Guides**: Inspiring, empowering (font-weight: 600)

### Spacing & Rhythm

```css
/* Sacred Geometry (8px base) */
--quest-space-breath: 0.25rem;   /* 4px - Tight grouping */
--quest-space-pause: 0.5rem;     /* 8px - Related elements */
--quest-space-beat: 1rem;        /* 16px - Standard separation */
--quest-space-rest: 1.5rem;      /* 24px - Section breaks */
--quest-space-chapter: 3rem;     /* 48px - Major transitions */
```

### Motion & Animation

```css
/* Timing Functions */
--quest-ease-enter: cubic-bezier(0, 0, 0.2, 1);     /* Gentle arrival */
--quest-ease-exit: cubic-bezier(0.4, 0, 1, 1);      /* Soft departure */
--quest-ease-awaken: cubic-bezier(0.34, 1.56, 0.64, 1); /* Bounce/delight */

/* Durations */
--quest-instant: 150ms;          /* Immediate feedback */
--quest-quick: 300ms;            /* Standard transitions */
--quest-gentle: 600ms;           /* Thoughtful changes */
--quest-sacred: 3000ms;          /* Major revelations */
```

---

## 🎨 Component Patterns

### Professional Mirror Components

#### Timeline Node States
```typescript
interface TimelineNodeStates {
  dormant: {
    opacity: 0.3;
    scale: 0.8;
    glow: 'none';
    cursor: 'default';
  };
  
  past: {
    opacity: 0.6;
    scale: 1.0;
    glow: 'subtle';
    cursor: 'pointer';
    hover: { opacity: 0.8, scale: 1.05 };
  };
  
  present: {
    opacity: 1.0;
    scale: 1.2;
    glow: 'bright';
    cursor: 'pointer';
    animation: 'pulse';
    hover: { scale: 1.3, glow: 'intense' };
  };
  
  future: {
    opacity: 0.4;
    scale: 0.9;
    glow: 'shimmer';
    cursor: 'not-allowed';
    animation: 'float';
  };
}
```

#### Milestone Interaction Pattern
```css
.milestone-node {
  /* Base state */
  transition: all var(--quest-quick) var(--quest-ease-enter);
  
  /* Hover state */
  &:hover {
    transform: scale(1.1) translateY(-2px);
    filter: brightness(1.2);
  }
  
  /* Focus state (keyboard navigation) */
  &:focus {
    outline: 3px solid var(--quest-primary);
    outline-offset: 4px;
  }
  
  /* Active/Selected state */
  &[aria-selected="true"] {
    box-shadow: 0 0 20px var(--quest-primary);
    animation: selected-pulse 2s infinite;
  }
}
```

### Trinity Evolution Visualization

#### Trinity States Through Time
```typescript
interface TrinityVisualization {
  past: {
    constellation: 'forming';
    opacity: 0.5;
    connections: 'dotted';
    label: 'What drove you then';
  };
  
  present: {
    constellation: 'active';
    opacity: 1.0;
    connections: 'solid';
    label: 'What drives you now';
    glow: true;
  };
  
  future: {
    constellation: 'crystallizing';
    opacity: 0.7;
    connections: 'gradient';
    label: 'Your emerging Quest';
    animation: 'shimmer';
  };
}
```

### Coach Presence Patterns

#### Coach Avatar States
```css
/* Coach appearance animation */
@keyframes coach-arrival {
  0% { 
    opacity: 0; 
    transform: scale(0.8) translateY(10px);
  }
  50% { 
    opacity: 0.8; 
    transform: scale(1.05) translateY(-2px);
  }
  100% { 
    opacity: 1; 
    transform: scale(1) translateY(0);
  }
}

.coach-avatar {
  animation: coach-arrival var(--quest-gentle) var(--quest-ease-awaken);
}
```

### Quest Readiness Indicators

#### Three-State System
```typescript
interface ReadinessStates {
  ready: {
    color: '--quest-ready';
    icon: 'check-circle';
    animation: 'celebrate';
    message: 'Your Quest awaits';
    ctaEnabled: true;
  };
  
  preparing: {
    color: '--quest-preparing';
    icon: 'clock';
    animation: 'progress';
    message: 'Your Quest is forming';
    ctaEnabled: false;
    showProgress: true;
  };
  
  notYet: {
    color: '--quest-not-yet';
    icon: 'compass';
    animation: 'float';
    message: 'Continue your story';
    ctaEnabled: false;
    showGuidance: true;
  };
}
```

---

## ♿ Accessibility Standards

### WCAG 2.1 AA Compliance

#### Core Requirements
1. **Perceivable**
   - Text contrast: 4.5:1 minimum (7:1 for enhanced)
   - Images: Alt text for all meaningful images
   - Audio/Video: Captions and transcripts
   - Color: Never sole indicator of meaning

2. **Operable**
   - Keyboard: All interactive elements keyboard accessible
   - Touch targets: 44x44px minimum
   - Timing: User control over timed content
   - Navigation: Skip links and landmarks

3. **Understandable**
   - Language: Simple, clear instructions
   - Errors: Clear identification and recovery
   - Help: Context-sensitive guidance
   - Consistency: Predictable patterns

4. **Robust**
   - Semantic HTML: Proper element usage
   - ARIA: Appropriate labels and roles
   - Compatibility: Works with assistive tech

### Quest-Specific Accessibility

#### Professional Mirror
```html
<!-- Accessible timeline structure -->
<nav role="navigation" aria-label="Your professional journey">
  <ol class="timeline" role="list">
    <li role="listitem" aria-current="step">
      <button 
        aria-label="Education at MIT, 2015-2019" 
        aria-describedby="milestone-details-1"
        aria-expanded="false"
      >
        <span class="visually-hidden">Past milestone:</span>
        MIT Education
      </button>
    </li>
  </ol>
</nav>
```

#### Trinity Discovery
```html
<!-- Accessible Trinity presentation -->
<section aria-labelledby="trinity-heading">
  <h2 id="trinity-heading">Your Trinity Evolution</h2>
  
  <div role="tablist" aria-label="Trinity through time">
    <button role="tab" aria-selected="true" aria-controls="past-panel">
      Past Trinity
    </button>
    <button role="tab" aria-selected="false" aria-controls="present-panel">
      Present Trinity
    </button>
    <button role="tab" aria-selected="false" aria-controls="future-panel">
      Future Trinity
    </button>
  </div>
  
  <div role="tabpanel" id="past-panel" aria-labelledby="past-tab">
    <!-- Past Trinity content -->
  </div>
</section>
```

#### Screen Reader Announcements
```typescript
// Live region for dynamic updates
const announceProgress = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
  const liveRegion = document.getElementById('quest-announcements');
  liveRegion.setAttribute('aria-live', priority);
  liveRegion.textContent = message;
};

// Usage examples
announceProgress('Story milestone added: First job at Google');
announceProgress('Trinity pattern recognized', 'assertive');
announceProgress('Quest readiness: Preparing. 2 areas need attention.');
```

---

## 🎭 Interaction Patterns

### Story Collection Flow

#### Progressive Disclosure
```typescript
interface StoryInteraction {
  initial: {
    show: ['education', 'current_role'];
    hide: ['details', 'connections', 'insights'];
  };
  
  engaged: {
    show: ['all_milestones', 'basic_connections'];
    hide: ['deep_insights', 'trinity_patterns'];
  };
  
  invested: {
    show: ['everything'];
    specialEffects: ['constellation_forming', 'pattern_highlighting'];
  };
}
```

#### Correction Interface
```css
/* Inline editing pattern */
.milestone-correction {
  /* Strike-through original */
  .original-data {
    text-decoration: line-through;
    opacity: 0.5;
  }
  
  /* Highlight correction */
  .corrected-data {
    color: var(--quest-primary);
    border-bottom: 2px solid var(--quest-primary);
    animation: correction-glow 1s ease-out;
  }
  
  /* Celebration animation */
  @keyframes correction-glow {
    0%, 100% { box-shadow: none; }
    50% { box-shadow: 0 0 10px var(--quest-primary); }
  }
}
```

### Trinity Evolution Animation

```css
/* Trinity constellation morphing */
@keyframes trinity-evolution {
  /* Past state */
  0% {
    filter: blur(2px) opacity(0.5);
    transform: scale(0.9);
  }
  
  /* Present state */
  50% {
    filter: blur(0) opacity(1);
    transform: scale(1);
  }
  
  /* Future state */
  100% {
    filter: blur(0) opacity(0.8);
    transform: scale(1.1);
    box-shadow: 0 0 30px var(--quest-future);
  }
}

.trinity-constellation {
  animation: trinity-evolution var(--quest-sacred) var(--quest-ease-enter);
}
```

### Quest Readiness Gate

#### Visual Feedback Sequence
```typescript
interface ReadinessAnimation {
  calculating: {
    duration: 2000;
    stages: [
      { percent: 0, message: 'Analyzing your story...' },
      { percent: 33, message: 'Recognizing patterns...' },
      { percent: 66, message: 'Assessing Trinity clarity...' },
      { percent: 100, message: 'Determining readiness...' }
    ];
  };
  
  revealing: {
    duration: 1000;
    effect: 'fade_and_scale';
    celebration: boolean; // true if ready
  };
}
```

---

## 🧪 Playwright MCP Testing Specifications

### Visual Regression Tests

#### Component State Validation
```typescript
// Playwright test for Professional Mirror states
test('Professional Mirror timeline states', async ({ page }) => {
  await page.goto('/story/mirror');
  
  // Test past node styling
  const pastNode = page.locator('[data-timeline-period="past"]').first();
  await expect(pastNode).toHaveCSS('opacity', '0.6');
  await expect(pastNode).toHaveCSS('cursor', 'pointer');
  
  // Test hover state
  await pastNode.hover();
  await expect(pastNode).toHaveCSS('opacity', '0.8');
  await expect(pastNode).toHaveCSS('transform', /scale\(1\.05\)/);
  
  // Test present node animation
  const presentNode = page.locator('[data-timeline-period="present"]');
  await expect(presentNode).toHaveCSS('animation-name', 'pulse');
});
```

#### Accessibility Validation
```typescript
// Playwright accessibility test suite
test.describe('Quest Core V2 Accessibility', () => {
  test('Professional Mirror keyboard navigation', async ({ page }) => {
    await page.goto('/story/mirror');
    
    // Tab through timeline
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toHaveAttribute('role', 'button');
    await expect(page.locator(':focus')).toHaveCSS('outline-width', '3px');
    
    // Activate with Enter
    await page.keyboard.press('Enter');
    await expect(page.locator('[aria-expanded="true"]')).toBeVisible();
  });
  
  test('Screen reader announcements', async ({ page }) => {
    await page.goto('/story/mirror');
    
    // Check live region exists
    const liveRegion = page.locator('[aria-live]');
    await expect(liveRegion).toBeAttached();
    
    // Trigger milestone interaction
    await page.click('[data-milestone-id="1"]');
    
    // Verify announcement
    await expect(liveRegion).toContainText(/milestone/i);
  });
});
```

#### Animation Performance
```typescript
// Test animation performance
test('Trinity evolution animation performance', async ({ page }) => {
  await page.goto('/trinity/evolution');
  
  // Start performance measurement
  await page.evaluate(() => performance.mark('animation-start'));
  
  // Trigger animation
  await page.click('[data-trigger="evolve-trinity"]');
  
  // Measure frame rate during animation
  const metrics = await page.evaluate(async () => {
    await new Promise(resolve => setTimeout(resolve, 3000));
    performance.mark('animation-end');
    performance.measure('trinity-animation', 'animation-start', 'animation-end');
    
    const measure = performance.getEntriesByName('trinity-animation')[0];
    return measure;
  });
  
  // Ensure smooth 60fps (16.67ms per frame)
  expect(metrics.duration / 180).toBeLessThan(17); // 3 seconds = ~180 frames
});
```

### Interaction Flow Tests

#### Story Collection Journey
```typescript
test('Complete story collection flow', async ({ page }) => {
  await page.goto('/story/begin');
  
  // Test progressive disclosure
  const initialMilestones = page.locator('[data-milestone]');
  await expect(initialMilestones).toHaveCount(2); // Only education and current
  
  // Engage with content
  await page.click('[data-milestone="education"]');
  await page.fill('[data-correction-field]', 'MIT, Computer Science');
  
  // Verify more milestones appear
  await expect(initialMilestones).toHaveCount(5); // More history revealed
  
  // Check visual feedback
  await expect(page.locator('.correction-celebration')).toBeVisible();
});
```

#### Trinity Recognition
```typescript
test('Trinity pattern recognition', async ({ page }) => {
  await page.goto('/trinity/discover');
  
  // Verify trinity states
  const pastTrinity = page.locator('[data-trinity-time="past"]');
  const presentTrinity = page.locator('[data-trinity-time="present"]');
  const futureTrinity = page.locator('[data-trinity-time="future"]');
  
  // Check opacity progression
  await expect(pastTrinity).toHaveCSS('opacity', '0.5');
  await expect(presentTrinity).toHaveCSS('opacity', '1');
  await expect(futureTrinity).toHaveCSS('opacity', '0.7');
  
  // Test constellation animation
  await expect(futureTrinity).toHaveCSS('animation-name', 'shimmer');
});
```

#### Readiness Gate
```typescript
test('Quest readiness assessment', async ({ page }) => {
  await page.goto('/quest/readiness');
  
  // Test calculating animation
  const progressBar = page.locator('[role="progressbar"]');
  await expect(progressBar).toHaveAttribute('aria-valuenow', '0');
  
  // Wait for calculation
  await page.waitForSelector('[data-readiness-result]', { timeout: 5000 });
  
  // Verify appropriate styling based on result
  const result = await page.getAttribute('[data-readiness-result]', 'data-status');
  
  if (result === 'ready') {
    await expect(page.locator('.readiness-indicator')).toHaveCSS('color', 'rgb(16, 185, 129)');
    await expect(page.locator('[data-cta="begin-quest"]')).toBeEnabled();
  } else if (result === 'preparing') {
    await expect(page.locator('.readiness-indicator')).toHaveCSS('color', 'rgb(245, 158, 11)');
    await expect(page.locator('[data-progress-indicator]')).toBeVisible();
  }
});
```

### Design Token Validation

```typescript
// Validate design tokens are applied correctly
test('Design token consistency', async ({ page }) => {
  await page.goto('/');
  
  // Check CSS variables
  const primaryColor = await page.evaluate(() => 
    getComputedStyle(document.documentElement).getPropertyValue('--quest-primary')
  );
  expect(primaryColor.trim()).toBe('#00D4B8');
  
  // Check typography scale
  const h1Size = await page.locator('h1').first().evaluate(el => 
    window.getComputedStyle(el).fontSize
  );
  expect(h1Size).toBe('48px'); // --quest-text-truth
  
  // Check spacing consistency
  const cardPadding = await page.locator('.quest-card').first().evaluate(el => 
    window.getComputedStyle(el).padding
  );
  expect(cardPadding).toBe('24px'); // --quest-space-rest
});
```

---

## 📱 Responsive Design

### Breakpoint System

```css
/* Mobile-first breakpoints */
--quest-screen-sm: 640px;   /* Phone landscape */
--quest-screen-md: 768px;   /* Tablet portrait */
--quest-screen-lg: 1024px;  /* Tablet landscape */
--quest-screen-xl: 1280px;  /* Desktop */
--quest-screen-2xl: 1536px; /* Wide desktop */
```

### Responsive Patterns

#### Professional Mirror Adaptation
```css
/* Mobile: Vertical timeline */
@media (max-width: 767px) {
  .timeline {
    flex-direction: column;
    
    .milestone-node {
      width: 100%;
      margin: var(--quest-space-beat) 0;
    }
  }
}

/* Tablet: Diagonal timeline */
@media (min-width: 768px) and (max-width: 1023px) {
  .timeline {
    transform: rotate(-15deg);
    
    .milestone-content {
      transform: rotate(15deg); /* Counter-rotate content */
    }
  }
}

/* Desktop: Horizontal timeline */
@media (min-width: 1024px) {
  .timeline {
    flex-direction: row;
    justify-content: space-between;
  }
}
```

#### Touch Optimization
```css
/* Ensure 44x44px touch targets */
.touch-target {
  min-width: 44px;
  min-height: 44px;
  
  /* Add padding if content is smaller */
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    inset: -8px; /* Expand touch area */
  }
}
```

---

## 🎨 Motion & Animation Guidelines

### Core Animation Principles

1. **Purposeful**: Every animation serves the user journey
2. **Respectful**: Honor motion preferences
3. **Smooth**: Maintain 60fps performance
4. **Delightful**: Add joy without distraction

### Animation Patterns

#### Entry Animations
```css
/* Gentle fade and scale */
@keyframes sacred-enter {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Usage */
.coach-message {
  animation: sacred-enter var(--quest-gentle) var(--quest-ease-enter);
}
```

#### Continuous Animations
```css
/* Breathing pulse for present state */
@keyframes gentle-pulse {
  0%, 100% { 
    transform: scale(1);
    opacity: 0.9;
  }
  50% { 
    transform: scale(1.05);
    opacity: 1;
  }
}

/* Shimmer for future potential */
@keyframes future-shimmer {
  0% { 
    background-position: -200% center;
  }
  100% { 
    background-position: 200% center;
  }
}
```

#### Celebration Animations
```css
/* Quest readiness celebration */
@keyframes quest-ready-celebration {
  0% { 
    transform: scale(1) rotate(0deg);
  }
  25% { 
    transform: scale(1.1) rotate(5deg);
  }
  50% { 
    transform: scale(1.05) rotate(-5deg);
  }
  75% { 
    transform: scale(1.1) rotate(3deg);
  }
  100% { 
    transform: scale(1) rotate(0deg);
  }
}
```

### Respecting Motion Preferences

```css
/* Reduce motion for users who prefer it */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  /* Keep essential feedback */
  .loading-spinner {
    animation-duration: 1s !important;
  }
}
```

---

## ✍️ Content Guidelines

### Voice & Tone

#### The Biographer (Story Phase)
- **Voice**: Warm, patient, curious
- **Tone**: "Tell me more about that..."
- **Never**: Rushed, judgmental, prescriptive

Example:
```
"I see you spent 4 years at Google. What drew you to that opportunity?"
NOT: "Why did you leave Google?"
```

#### The Pattern Seeker (Trinity Recognition)
- **Voice**: Insightful, connecting, revelatory  
- **Tone**: "Notice how this connects to..."
- **Never**: Forcing connections, oversimplifying

Example:
```
"Looking at your journey, I notice a pattern of seeking innovative challenges..."
NOT: "You always job-hop when bored."
```

#### The Quest Guides (Quest Phase)
- **Voice**: Inspiring, empowering, actionable
- **Tone**: "Based on your Trinity, consider..."
- **Never**: Generic advice, one-size-fits-all

Example:
```
"Your Quest to democratize AI education aligns with these three paths..."
NOT: "Here's what everyone in tech should do..."
```

### Microcopy Patterns

#### Error Messages
```typescript
interface ErrorMessage {
  issue: string;
  impact: string;
  recovery: string;
  tone: 'supportive';
}

// Example
{
  issue: "We couldn't retrieve your LinkedIn data",
  impact: "This means we'll need your help building your story",
  recovery: "Let's start with your education instead",
  tone: 'supportive'
}
```

#### Loading States
```typescript
const loadingMessages = [
  "Gathering your professional constellation...",
  "Recognizing patterns in your journey...",
  "Awakening your Trinity...",
  "Preparing your Quest..."
];
```

#### Empty States
```
No milestones yet? Every journey begins with a single step.
[Begin with your education]
```

---

## 🔍 Testing Checklist

### Visual Testing
- [ ] All components match design tokens
- [ ] Animations perform at 60fps
- [ ] Touch targets meet 44x44px minimum
- [ ] Focus states visible and accessible
- [ ] Color contrast passes WCAG AA

### Interaction Testing
- [ ] Keyboard navigation works throughout
- [ ] Screen reader announcements appropriate
- [ ] Progressive disclosure functions correctly
- [ ] Error recovery paths clear
- [ ] Loading states informative

### Responsive Testing
- [ ] Mobile layout functional
- [ ] Tablet adaptations appropriate
- [ ] Desktop experience optimal
- [ ] Touch interactions smooth
- [ ] Text remains readable at all sizes

### Performance Testing
- [ ] Animations maintain 60fps
- [ ] Page loads under 3 seconds
- [ ] Interactions respond within 100ms
- [ ] Memory usage stays reasonable
- [ ] No layout shifts during load

---

## 🚀 Implementation Priorities

### Phase 1: Foundation
1. Implement design tokens in CSS/Tailwind
2. Create base component library
3. Set up Playwright MCP tests
4. Validate accessibility baseline

### Phase 2: Sacred Journey Components
1. Professional Mirror timeline
2. Trinity evolution visualization
3. Coach interaction patterns
4. Quest readiness indicators

### Phase 3: Polish & Delight
1. Animation refinements
2. Celebration moments
3. Advanced accessibility features
4. Performance optimizations

---

## 📚 Resources

### Design References
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [Inclusive Design Principles](https://inclusivedesignprinciples.org/)

### Testing Tools
- Playwright MCP for automated testing
- Axe DevTools for accessibility audit
- Chrome DevTools for performance profiling

### Quest Core Specific
- `QUEST_CORE_MANIFESTO.md` - Our philosophical foundation
- `V2_PROFESSIONAL_MIRROR_DESIGN.md` - Detailed mirror specifications
- `DESIGN_SYSTEM.md` - Component specifications
- `DESIGN_TOKENS.md` - Token definitions

---

*"In the mirror of technology, we see not just interfaces, but the sacred journey of human potential."*

**Quest Core V2 Style Guide © 2025 - Where design serves awakening**