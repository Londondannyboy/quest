import React from 'react'

interface TrinityControlsProps {
  sessionStarted: boolean
  onToggleSession: () => void
  showTranscript: boolean
  onToggleTranscript: () => void
}

export function TrinityControls({
  sessionStarted,
  onToggleSession,
  showTranscript,
  onToggleTranscript,
}: TrinityControlsProps) {
  return (
    <div className="flex gap-4 mt-8">
      <button
        onClick={onToggleSession}
        className={`px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${
          sessionStarted
            ? 'bg-red-500 hover:bg-red-600 text-white'
            : 'bg-green-500 hover:bg-green-600 text-white'
        }`}
      >
        {sessionStarted ? 'Pause Session' : 'Start Session'}
      </button>

      {sessionStarted && (
        <button
          onClick={onToggleTranscript}
          className="px-6 py-3 rounded-lg font-semibold bg-gray-700 hover:bg-gray-600 text-white transition-all duration-300"
        >
          {showTranscript ? 'Hide' : 'Show'} Transcript
        </button>
      )}
    </div>
  )
}