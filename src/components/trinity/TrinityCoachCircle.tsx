import React from 'react'

interface CoachInfo {
  name: string
  color: string
  icon: string
}

interface TrinityCoachCircleProps {
  isListening: boolean
  isConnected: boolean
  sessionStarted: boolean
  coachInfo: CoachInfo
  onToggleListening: () => void
}

export function TrinityCoachCircle({
  isListening,
  isConnected,
  sessionStarted,
  coachInfo,
  onToggleListening,
}: TrinityCoachCircleProps) {
  const getStatusText = () => {
    if (!sessionStarted) return 'Start Session First'
    if (!isConnected) return 'Connecting...'
    if (isListening) return 'Listening...'
    return 'Click to Speak'
  }

  return (
    <div className="relative">
      {/* Outer glow */}
      <div
        className={`absolute inset-0 rounded-full opacity-20 blur-3xl transition-all duration-1000 ${
          isListening ? 'scale-150' : 'scale-100'
        } ${
          coachInfo.color === 'purple'
            ? 'bg-purple-500'
            : coachInfo.color === 'blue'
            ? 'bg-blue-500'
            : 'bg-green-500'
        }`}
      />

      {/* Main circle button */}
      <button
        onClick={onToggleListening}
        disabled={!isConnected || !sessionStarted}
        className={`relative w-64 h-64 rounded-full transition-all duration-300 ${
          isListening ? 'scale-110' : 'scale-100 hover:scale-105'
        } ${
          !isConnected || !sessionStarted
            ? 'bg-gray-700 cursor-not-allowed'
            : coachInfo.color === 'purple'
            ? 'bg-gradient-to-br from-purple-600 to-purple-800'
            : coachInfo.color === 'blue'
            ? 'bg-gradient-to-br from-blue-600 to-blue-800'
            : 'bg-gradient-to-br from-green-600 to-green-800'
        } shadow-2xl flex flex-col items-center justify-center`}
      >
        <span className="text-6xl mb-4">{coachInfo.icon}</span>
        <span className="text-xl font-semibold">{getStatusText()}</span>
      </button>

      {/* Pulse animation when listening */}
      {isListening && isConnected && (
        <div className="absolute inset-0 rounded-full animate-ping opacity-20 bg-white" />
      )}
    </div>
  )
}