# V3 News & Voice UI Design Strategy

*Last Updated: December 2024*

## Overview

Integrating a news platform with conversational AI presents unique design challenges. This document outlines how to create a cohesive experience that serves both information consumption and interactive coaching.

## Design Philosophy

### Core Principles
1. **Content-First, Voice-Enhanced**: News is primary, voice adds value
2. **Progressive Disclosure**: Start simple, reveal complexity through interaction
3. **Contextual Intelligence**: Voice UI adapts based on user activity
4. **Seamless Transitions**: Natural flow between reading and conversing

## UI Architecture

### Layout Strategy

```
┌─────────────────────────────────────────────────────────┐
│                    Navigation Bar                         │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────┐  ┌─────────────────────┐   │
│  │                         │  │                     │   │
│  │     News Content        │  │   Voice Assistant   │   │
│  │     (Primary View)      │  │   (Collapsible)    │   │
│  │                         │  │                     │   │
│  │  - Articles             │  │  - Trinity Discovery│   │
│  │  - Analysis             │  │  - Quick Questions  │   │
│  │  - Market Updates       │  │  - Contextual Help  │   │
│  │                         │  │                     │   │
│  └─────────────────────────┘  └─────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Responsive Modes

**Desktop (>1024px)**
- Split view: 70% content, 30% voice assistant
- Voice panel can minimize to floating button
- News sidebar for categories/filters

**Tablet (768-1024px)**
- Content primary with voice overlay
- Voice activates as modal/drawer
- Swipe gestures between modes

**Mobile (<768px)**
- Content-only default view
- Voice button fixed bottom-right
- Full-screen voice when activated

## Voice Integration Patterns

### 1. Contextual Voice Assistant

```typescript
// Voice understands current context
interface VoiceContext {
  currentPage: 'news' | 'article' | 'investor-profile'
  activeContent: {
    type: string
    id: string
    metadata: any
  }
  userRole: 'founder' | 'investor' | 'journalist'
}

// Examples of contextual responses:
// On funding news: "Want to know how to approach these investors?"
// On market analysis: "Should I explain how this affects your startup?"
// On investor profile: "Would you like help crafting a pitch?"
```

### 2. Reading Enhancement

**Voice-Activated Features**
- "Summarize this article"
- "Explain this in simpler terms"
- "How does this relate to my startup?"
- "Find similar articles"
- "Save this for later"

**Visual Indicators**
```css
/* Active voice listening state */
.article-content.voice-active {
  border-left: 3px solid var(--quest-primary);
  background: linear-gradient(90deg, 
    rgba(0, 212, 184, 0.05) 0%, 
    transparent 10%
  );
}

/* Highlighted content being discussed */
.voice-highlight {
  background: rgba(0, 212, 184, 0.1);
  border-radius: 4px;
  transition: all 0.3s ease;
}
```

### 3. News-Specific Voice Commands

```typescript
const newsVoiceCommands = {
  navigation: [
    "Show me funding news",
    "What's trending today?",
    "Find articles about [topic]"
  ],
  
  analysis: [
    "Analyze this investor's portfolio",
    "Compare these funding rounds",
    "What's the trend in [industry]?"
  ],
  
  actions: [
    "Draft a pitch for this investor",
    "Schedule time to read this",
    "Share this with my team"
  ]
}
```

## Design Components

### 1. Voice Button States

```typescript
// Floating action button with contextual states
export function VoiceButton({ context }: { context: VoiceContext }) {
  const [state, setState] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle')
  
  return (
    <button className={`
      fixed bottom-6 right-6 z-50
      w-16 h-16 rounded-full
      shadow-lg transition-all duration-300
      ${state === 'idle' ? 'bg-quest-primary hover:scale-110' : ''}
      ${state === 'listening' ? 'bg-red-500 animate-pulse' : ''}
      ${state === 'thinking' ? 'bg-quest-secondary animate-spin' : ''}
      ${state === 'speaking' ? 'bg-quest-primary animate-bounce' : ''}
    `}>
      <VoiceIcon state={state} />
      {context.currentPage === 'article' && (
        <span className="absolute -top-2 -right-2 bg-quest-accent text-white text-xs rounded-full px-2">
          Ask about article
        </span>
      )}
    </button>
  )
}
```

### 2. News Layout with Voice Panel

```typescript
export function NewsLayout({ children }: { children: React.ReactNode }) {
  const [voicePanelOpen, setVoicePanelOpen] = useState(false)
  
  return (
    <div className="flex h-screen">
      {/* Main content area */}
      <main className={`
        flex-1 transition-all duration-300
        ${voicePanelOpen ? 'mr-96' : 'mr-0'}
      `}>
        {children}
      </main>
      
      {/* Voice panel */}
      <aside className={`
        fixed right-0 top-0 h-full
        w-96 bg-gray-900 border-l border-gray-800
        transform transition-transform duration-300
        ${voicePanelOpen ? 'translate-x-0' : 'translate-x-full'}
      `}>
        <VoiceInterface />
      </aside>
      
      {/* Voice toggle button */}
      <VoiceButton 
        context={useVoiceContext()}
        onClick={() => setVoicePanelOpen(!voicePanelOpen)}
      />
    </div>
  )
}
```

### 3. Article Enhancement

```typescript
export function ArticleView({ article }: { article: NewsArticle }) {
  const [voiceHighlights, setVoiceHighlights] = useState<string[]>([])
  
  return (
    <article className="max-w-4xl mx-auto px-6 py-12">
      {/* Article header */}
      <header className="mb-8">
        <h1 className="text-4xl font-bold mb-4">{article.headline}</h1>
        <div className="flex items-center gap-4 text-gray-400">
          <span>{article.publishedAt}</span>
          <span>•</span>
          <span>{article.readTime} min read</span>
          <VoiceReadButton articleId={article.id} />
        </div>
      </header>
      
      {/* Enhanced content with voice highlights */}
      <div className="prose prose-lg">
        <ContentRenderer 
          content={article.content}
          highlights={voiceHighlights}
        />
      </div>
      
      {/* Voice-powered related content */}
      <VoiceRecommendations 
        context={{
          article: article.id,
          userInterests: useUserProfile().interests
        }}
      />
    </article>
  )
}
```

## Voice UI Components

### 1. Minimized State (Reading Mode)

```typescript
export function VoiceMinimized() {
  return (
    <div className="fixed bottom-6 right-6 bg-gray-900 rounded-full p-4 shadow-xl">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-full bg-quest-primary/20 flex items-center justify-center">
          <MicrophoneIcon className="w-6 h-6 text-quest-primary" />
        </div>
        <span className="text-sm text-gray-400">Ask Quest AI</span>
      </div>
    </div>
  )
}
```

### 2. Expanded State (Conversation Mode)

```typescript
export function VoiceExpanded() {
  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="p-6 border-b border-gray-800">
        <h3 className="text-xl font-semibold">Quest AI Assistant</h3>
        <p className="text-gray-400 text-sm">I can help you understand and act on news</p>
      </div>
      
      {/* Conversation */}
      <div className="flex-1 overflow-y-auto p-6">
        <ConversationHistory />
      </div>
      
      {/* Voice input */}
      <div className="p-6 border-t border-gray-800">
        <VoiceInput />
      </div>
    </div>
  )
}
```

### 3. Smart Suggestions

```typescript
export function VoiceSuggestions({ context }: { context: VoiceContext }) {
  const suggestions = useVoiceSuggestions(context)
  
  return (
    <div className="grid gap-2 p-4">
      <p className="text-sm text-gray-400 mb-2">Try asking:</p>
      {suggestions.map((suggestion, i) => (
        <button
          key={i}
          className="text-left p-3 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
          onClick={() => handleVoiceCommand(suggestion.command)}
        >
          <span className="text-quest-primary text-sm">{suggestion.icon}</span>
          <span className="ml-2 text-sm">{suggestion.text}</span>
        </button>
      ))}
    </div>
  )
}

// Context-aware suggestions
function useVoiceSuggestions(context: VoiceContext) {
  if (context.currentPage === 'article') {
    return [
      { icon: '📝', text: 'Summarize this article', command: 'summarize' },
      { icon: '🎯', text: 'How does this relate to my startup?', command: 'relate' },
      { icon: '📧', text: 'Draft an email to this investor', command: 'draft-email' }
    ]
  }
  
  if (context.currentPage === 'news') {
    return [
      { icon: '🔥', text: "What's trending in my industry?", command: 'trending' },
      { icon: '💰', text: 'Show recent funding rounds', command: 'funding' },
      { icon: '👤', text: 'Find investors in my space', command: 'investors' }
    ]
  }
  
  return []
}
```

## Mobile-First Considerations

### Touch Interactions
- Swipe up to expand voice panel
- Swipe down to minimize
- Long press article text to ask about it
- Double tap to bookmark with voice note

### Voice Activation
```typescript
export function MobileVoiceActivation() {
  const [isActive, setIsActive] = useState(false)
  
  return (
    <>
      {/* Bottom sheet style */}
      <div className={`
        fixed inset-x-0 bottom-0 z-50
        bg-gray-900 rounded-t-3xl
        transform transition-transform duration-300
        ${isActive ? 'translate-y-0' : 'translate-y-[calc(100%-5rem)]'}
      `}>
        {/* Handle bar */}
        <div className="w-12 h-1 bg-gray-600 rounded-full mx-auto mt-3" />
        
        {/* Minimized view */}
        <div className="p-6">
          <button 
            className="w-full flex items-center justify-center gap-3"
            onClick={() => setIsActive(!isActive)}
          >
            <div className="w-12 h-12 rounded-full bg-quest-primary animate-pulse" />
            <span>Tap to ask Quest AI</span>
          </button>
        </div>
        
        {/* Expanded view */}
        {isActive && (
          <div className="h-[70vh] px-6 pb-6">
            <VoiceInterface mobile />
          </div>
        )}
      </div>
    </>
  )
}
```

## Animation & Transitions

### Voice State Animations
```css
/* Listening state - gentle pulse */
@keyframes voice-listening {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

/* Thinking state - rotating gradient */
@keyframes voice-thinking {
  0% { background-position: 0% 50%; }
  100% { background-position: 100% 50%; }
}

/* Speaking state - sound waves */
@keyframes voice-speaking {
  0% { transform: scaleY(0.5); }
  50% { transform: scaleY(1); }
  100% { transform: scaleY(0.5); }
}

.voice-wave {
  animation: voice-speaking 0.3s ease-in-out infinite;
  animation-delay: calc(var(--wave-index) * 0.1s);
}
```

### Content Highlighting
```typescript
export function HighlightAnimation({ children, active }: any) {
  return (
    <span className={`
      relative inline-block
      transition-all duration-500 ease-out
      ${active ? 'text-quest-primary' : ''}
    `}>
      {active && (
        <span className="
          absolute inset-0 -inset-x-2 -inset-y-1
          bg-quest-primary/10 rounded
          animate-highlight-fade
        " />
      )}
      {children}
    </span>
  )
}
```

## Accessibility

### Voice UI Accessibility
- Keyboard navigation for all voice features
- Screen reader announcements for voice state changes
- Visual indicators for audio feedback
- Transcript availability for all voice interactions
- Fallback text input option

### ARIA Labels
```typescript
<button
  aria-label="Activate voice assistant"
  aria-pressed={isVoiceActive}
  aria-live="polite"
  aria-atomic="true"
>
  <span className="sr-only">
    {isVoiceActive ? 'Voice assistant is listening' : 'Click to activate voice'}
  </span>
</button>
```

## Performance Optimization

### Lazy Loading
- Voice UI components load on-demand
- Audio processing runs in Web Worker
- Transcripts cache locally
- Gradual enhancement based on connection

### Resource Management
```typescript
// Only load voice UI when needed
const VoiceInterface = lazy(() => import('./VoiceInterface'))

// Preload voice resources on hover
function preloadVoiceResources() {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      import('./voice-processor')
      new Audio('/sounds/voice-activate.mp3')
    })
  }
}
```

## Design System Integration

### Quest Brand in News Context
- Maintain Quest color system
- Voice UI uses accent colors
- News content stays neutral
- Interactive elements use brand colors

### Typography Hierarchy
```css
/* News content - professional */
.news-article {
  font-family: 'Inter', system-ui;
  color: var(--gray-100);
}

/* Voice UI - friendly */
.voice-interface {
  font-family: 'GT Walsheim', sans-serif;
  color: var(--quest-primary);
}
```

## Future Enhancements

### Advanced Features
1. **Voice Navigation**: "Next article about AI funding"
2. **Multi-Modal**: Point camera at article, ask questions
3. **Collaborative**: Share voice sessions with team
4. **Predictive**: Suggest articles before asking
5. **Ambient Mode**: Background listening for opportunities

### AR/VR Considerations
- Voice-first in AR glasses
- Spatial audio for news categories
- Gesture controls for voice activation
- 3D data visualizations with voice

---

*"Where news meets intelligence - Quest V3 brings conversational AI to content."*