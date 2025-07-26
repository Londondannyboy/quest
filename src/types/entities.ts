// Entity types for Quest Core V2
// Philosophy: Everything is an entity, no raw strings

export interface ProfessionalMirrorData {
  visualization: "Timeline with floating nodes"
  messaging: "This is how the world sees you"
  corrections: "Click any node to correct our understanding"
  transparency: "Here's what we found (and might have missed)"
}

export interface TrinityEvolution {
  past: {
    quest: string | null
    service: string | null
    pledge: string | null
    visual: "Faded constellation forming"
  }
  present: {
    quest: string | null
    service: string | null
    pledge: string | null
    visual: "Bright, active constellation"
  }
  future: {
    quest: string | null
    service: string | null
    pledge: string | null
    visual: "Emerging, pulsing constellation"
  }
}

export interface VoiceTransition {
  trigger: "Trinity clarity reached" | "Quest readiness achieved"
  effect: "Signature sound + brief silence"
  announcement: "New coach introduces themselves"
  continuity: "References previous coach's insights"
}

export interface SyntheticEntity {
  type: "company" | "person" | "skill"
  confidence: number  // AI confidence in accuracy
  status: "provisional" | "validated" | "rejected"
  validators: string[]  // User IDs who confirmed
  created: Date
  source: "linkedin" | "tavily" | "user"
}

export interface SkillClusterData {
  name: string
  coreSkills: string[]
  emergingSkills: string[]
  parentCluster: string
  demandTrend: "increasing" | "stable" | "decreasing"
  salaryPremium: number  // % above base
}

export interface ReadinessCalculation {
  storyDepth: number      // How much they shared (0-100)
  trinityClarity: number  // How clear their purpose (0-100)
  futureOrientation: number // How ready for growth (0-100)
  overall: number         // Weighted score
}

export type QuestOutcome = "QUEST_READY" | "PREPARING" | "NOT_YET"

export interface JourneyPhase {
  phase: "professional_mirror" | "trinity_discovery" | "quest_gate"
  startTime: Date
  completedTime?: Date
  metrics: {
    engagement: number
    depth: number
    clarity: number
  }
}