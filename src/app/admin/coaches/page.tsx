'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'

interface CoachPrompt {
  id: string
  name: string
  role: string
  personality: string
  conversationGuidelines: string
  examples: string
  backchanneling: string
  emotionalResponses: string
  voiceCharacteristics: string
  active: boolean
  createdAt: string
  updatedAt: string
}

const DEFAULT_COACHES: Omit<CoachPrompt, 'id' | 'createdAt' | 'updatedAt'>[] = [
  {
    name: 'Story Coach',
    role: 'A warm, empathetic Story Coach (biographer) who helps users discover their authentic professional story through deep listening and thoughtful questions.',
    personality: 'Warm, patient, and genuinely curious. Speaks with a gentle but purposeful tone, like a wise mentor who truly cares about understanding their story. Uses natural conversational markers like "I see", "Tell me more", and "That\'s fascinating".',
    conversationGuidelines: `
- Ask open-ended questions about transitions and choices
- Listen actively and reflect back what you hear
- Use minimal encouragers: "mmhm", "go on", "I understand"
- Allow for pauses and silence - don't rush to fill gaps
- Notice patterns without judging
- Draw out emotions and motivations
- Focus on the WHY behind career moves
- Create psychological safety for vulnerability`,
    examples: `
User: "I left my corporate job to start my own company."
Coach: "Oh wow, that must have been a big decision. What was happening in your life that led you to take that leap?"

User: "I've always struggled with feeling like I belong."
Coach: "Mmhm, I hear that. Tell me more about when you first noticed that feeling in your career."`,
    backchanneling: 'Use warm acknowledgments: "I see", "Yes", "That makes sense", "I hear you"',
    emotionalResponses: 'Match the user\'s emotional energy with empathy. If they\'re excited, share their enthusiasm. If they\'re struggling, offer gentle support.',
    voiceCharacteristics: 'Speak slowly and thoughtfully, with warm inflection. Use pauses effectively. Lower pitch slightly for gravitas.',
    active: true
  },
  {
    name: 'Quest Coach',
    role: 'An energetic Quest Coach (pattern seeker) who helps users recognize their Trinity evolution and connect the dots across their timeline.',
    personality: 'Enthusiastic, insightful, and inspiring. Speaks with energy and conviction, like a coach who sees your potential before you do. Uses phrases that build momentum and reveal patterns.',
    conversationGuidelines: `
- Connect dots across their timeline enthusiastically
- Highlight evolution from past to present to future
- Use pattern-revealing language: "I'm noticing...", "There's a thread here..."
- Build excitement about their potential
- Focus on transformation, not just information
- Celebrate insights and breakthroughs
- Help them see their highest possibilities
- Push them to dream bigger`,
    examples: `
User: "I keep coming back to education in different forms."
Coach: "Yes! I see that pattern emerging - you're not just teaching, you're transforming how people learn. What if that's your Quest calling you forward?"

User: "I don't know if I'm ready for something bigger."
Coach: "But listen to what you just shared - every transition has prepared you for this moment. Your Trinity is already revealing itself!"`,
    backchanneling: 'Use energetic affirmations: "Yes!", "Exactly!", "That\'s it!", "Keep going!"',
    emotionalResponses: 'Maintain high positive energy. Be encouraging and affirming. Show excitement about their discoveries.',
    voiceCharacteristics: 'Speak with dynamic range, rising inflection for questions, strong emphasis on key insights. Faster pace than Story Coach.',
    active: true
  },
  {
    name: 'Delivery Coach',
    role: 'A firm, achievement-focused Delivery Coach who helps users turn insights into action with practical guidance and accountability.',
    personality: 'Direct, confident, and results-oriented. Speaks with authority and clarity, like a seasoned executive who gets things done. No-nonsense but still supportive.',
    conversationGuidelines: `
- Be direct and challenging (supportively)
- Focus on commitment and readiness
- Push for specificity - no vague answers
- Create urgency around action
- Set clear expectations and next steps
- Don't accept excuses or deflection
- Maintain high standards
- Challenge them to step up
- Keep returning to "What will you DO?"`,
    examples: `
User: "I think I might start reaching out to people next month."
Coach: "Next month? No. What specific person will you contact by end of day tomorrow? I need a name and a commitment."

User: "I want to make an impact somehow."
Coach: "Too vague. Impact how? On whom? By when? Let's get crystal clear on your first concrete step."`,
    backchanneling: 'Use brief, firm acknowledgments: "Good", "Right", "And?", "Be specific"',
    emotionalResponses: 'Maintain professional firmness. Show approval for concrete commitments. Express dissatisfaction with vagueness.',
    voiceCharacteristics: 'Speak with clear, decisive tone. Lower pitch for authority. Minimal vocal fry. Strong, confident delivery.',
    active: true
  }
]

export default function AdminCoachesPage() {
  const { user } = useUser()
  const router = useRouter()
  const [coaches, setCoaches] = useState<CoachPrompt[]>([])
  const [selectedCoach, setSelectedCoach] = useState<CoachPrompt | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Check admin access
  useEffect(() => {
    if (user && !user.publicMetadata?.isAdmin) {
      router.push('/')
    }
  }, [user, router])

  // Load coaches
  useEffect(() => {
    loadCoaches()
  }, [])

  const loadCoaches = async () => {
    try {
      const response = await fetch('/api/admin/coaches')
      if (response.ok) {
        const data = await response.json()
        setCoaches(data.coaches)
      }
    } catch (error) {
      console.error('Failed to load coaches:', error)
      // Load defaults if API fails
      setCoaches(DEFAULT_COACHES.map((coach, index) => ({
        ...coach,
        id: `default-${index}`,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      })))
    }
  }

  const handleSave = async () => {
    if (!selectedCoach) return
    
    setIsSaving(true)
    try {
      const response = await fetch('/api/admin/coaches', {
        method: selectedCoach.id.startsWith('new-') ? 'POST' : 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(selectedCoach)
      })
      
      if (response.ok) {
        await loadCoaches()
        setIsEditing(false)
      }
    } catch (error) {
      console.error('Failed to save coach:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleFieldChange = (field: keyof CoachPrompt, value: string | boolean) => {
    if (selectedCoach) {
      setSelectedCoach({
        ...selectedCoach,
        [field]: value,
        updatedAt: new Date().toISOString()
      })
    }
  }

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Coach Voice Prompt Management</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Coach List */}
          <div className="lg:col-span-1">
            <h2 className="text-xl font-semibold mb-4">Coaches</h2>
            <div className="space-y-2">
              {coaches.map(coach => (
                <button
                  key={coach.id}
                  onClick={() => {
                    setSelectedCoach(coach)
                    setIsEditing(false)
                  }}
                  className={`w-full text-left p-4 rounded-lg transition-colors ${
                    selectedCoach?.id === coach.id
                      ? 'bg-blue-600'
                      : 'bg-gray-800 hover:bg-gray-700'
                  }`}
                >
                  <div className="font-semibold">{coach.name}</div>
                  <div className="text-sm text-gray-400">
                    {coach.active ? 'Active' : 'Inactive'}
                  </div>
                </button>
              ))}
              
              <button
                onClick={() => {
                  const newCoach: CoachPrompt = {
                    id: `new-${Date.now()}`,
                    name: 'New Coach',
                    role: '',
                    personality: '',
                    conversationGuidelines: '',
                    examples: '',
                    backchanneling: '',
                    emotionalResponses: '',
                    voiceCharacteristics: '',
                    active: false,
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString()
                  }
                  setSelectedCoach(newCoach)
                  setIsEditing(true)
                }}
                className="w-full p-4 border-2 border-dashed border-gray-600 rounded-lg hover:border-gray-500 transition-colors"
              >
                + Add New Coach
              </button>
            </div>
          </div>

          {/* Coach Details */}
          <div className="lg:col-span-2">
            {selectedCoach ? (
              <div className="bg-gray-800 p-6 rounded-lg">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold">
                    {isEditing ? 'Edit Coach' : 'Coach Details'}
                  </h2>
                  <div className="space-x-2">
                    {!isEditing ? (
                      <button
                        onClick={() => setIsEditing(true)}
                        className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
                      >
                        Edit
                      </button>
                    ) : (
                      <>
                        <button
                          onClick={() => setIsEditing(false)}
                          className="px-4 py-2 bg-gray-600 rounded hover:bg-gray-700"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleSave}
                          disabled={isSaving}
                          className="px-4 py-2 bg-green-600 rounded hover:bg-green-700 disabled:opacity-50"
                        >
                          {isSaving ? 'Saving...' : 'Save'}
                        </button>
                      </>
                    )}
                  </div>
                </div>

                <div className="space-y-4">
                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium mb-1">Name</label>
                    <input
                      type="text"
                      value={selectedCoach.name}
                      onChange={(e) => handleFieldChange('name', e.target.value)}
                      disabled={!isEditing}
                      className="w-full px-3 py-2 bg-gray-700 rounded disabled:opacity-50"
                    />
                  </div>

                  {/* Active Status */}
                  <div>
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={selectedCoach.active}
                        onChange={(e) => handleFieldChange('active', e.target.checked)}
                        disabled={!isEditing}
                        className="rounded"
                      />
                      <span>Active</span>
                    </label>
                  </div>

                  {/* Role */}
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Role Description
                    </label>
                    <textarea
                      value={selectedCoach.role}
                      onChange={(e) => handleFieldChange('role', e.target.value)}
                      disabled={!isEditing}
                      rows={3}
                      className="w-full px-3 py-2 bg-gray-700 rounded disabled:opacity-50"
                    />
                  </div>

                  {/* Personality */}
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Personality & Tone
                    </label>
                    <textarea
                      value={selectedCoach.personality}
                      onChange={(e) => handleFieldChange('personality', e.target.value)}
                      disabled={!isEditing}
                      rows={3}
                      className="w-full px-3 py-2 bg-gray-700 rounded disabled:opacity-50"
                    />
                  </div>

                  {/* Conversation Guidelines */}
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Conversation Guidelines
                    </label>
                    <textarea
                      value={selectedCoach.conversationGuidelines}
                      onChange={(e) => handleFieldChange('conversationGuidelines', e.target.value)}
                      disabled={!isEditing}
                      rows={6}
                      className="w-full px-3 py-2 bg-gray-700 rounded disabled:opacity-50 font-mono text-sm"
                    />
                  </div>

                  {/* Examples */}
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Example Interactions
                    </label>
                    <textarea
                      value={selectedCoach.examples}
                      onChange={(e) => handleFieldChange('examples', e.target.value)}
                      disabled={!isEditing}
                      rows={6}
                      className="w-full px-3 py-2 bg-gray-700 rounded disabled:opacity-50 font-mono text-sm"
                    />
                  </div>

                  {/* Backchanneling */}
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Backchanneling & Encouragers
                    </label>
                    <textarea
                      value={selectedCoach.backchanneling}
                      onChange={(e) => handleFieldChange('backchanneling', e.target.value)}
                      disabled={!isEditing}
                      rows={2}
                      className="w-full px-3 py-2 bg-gray-700 rounded disabled:opacity-50"
                    />
                  </div>

                  {/* Emotional Responses */}
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Emotional Response Guidelines
                    </label>
                    <textarea
                      value={selectedCoach.emotionalResponses}
                      onChange={(e) => handleFieldChange('emotionalResponses', e.target.value)}
                      disabled={!isEditing}
                      rows={2}
                      className="w-full px-3 py-2 bg-gray-700 rounded disabled:opacity-50"
                    />
                  </div>

                  {/* Voice Characteristics */}
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Voice Characteristics
                    </label>
                    <textarea
                      value={selectedCoach.voiceCharacteristics}
                      onChange={(e) => handleFieldChange('voiceCharacteristics', e.target.value)}
                      disabled={!isEditing}
                      rows={2}
                      className="w-full px-3 py-2 bg-gray-700 rounded disabled:opacity-50"
                    />
                  </div>

                  {/* Timestamps */}
                  <div className="text-sm text-gray-400 pt-4 border-t border-gray-700">
                    <div>Created: {new Date(selectedCoach.createdAt).toLocaleString()}</div>
                    <div>Updated: {new Date(selectedCoach.updatedAt).toLocaleString()}</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-gray-800 p-6 rounded-lg text-center text-gray-400">
                Select a coach to view details
              </div>
            )}
          </div>
        </div>

        {/* Best Practices */}
        <div className="mt-12 bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Hume AI Voice Prompting Best Practices</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div>
              <h3 className="font-semibold text-blue-400 mb-2">Writing Effective Prompts</h3>
              <ul className="space-y-1 text-gray-300">
                <li>• Design for spoken output, not text</li>
                <li>• Use natural conversational language</li>
                <li>• Keep prompts 2000-5000 tokens</li>
                <li>• Include discourse markers (&quot;oh&quot;, &quot;well&quot;, &quot;you know&quot;)</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-blue-400 mb-2">Voice Characteristics</h3>
              <ul className="space-y-1 text-gray-300">
                <li>• Use few-shot examples for personality</li>
                <li>• Specify tone explicitly</li>
                <li>• Guide emotional responsiveness</li>
                <li>• Consider vocal expression measurements</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-blue-400 mb-2">Conversation Flow</h3>
              <ul className="space-y-1 text-gray-300">
                <li>• Implement backchanneling (&quot;mmhm&quot;, &quot;I see&quot;)</li>
                <li>• Avoid interrupting users</li>
                <li>• Support natural turn-taking</li>
                <li>• Allow for pauses and silence</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-blue-400 mb-2">Personality Types</h3>
              <ul className="space-y-1 text-gray-300">
                <li>• Define clear persona characteristics</li>
                <li>• Adapt to emotional cues</li>
                <li>• Provide context-specific responses</li>
                <li>• Enable emotional intelligence</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}