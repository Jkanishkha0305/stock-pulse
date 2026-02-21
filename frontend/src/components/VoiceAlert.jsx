import { useRef, useEffect } from 'react'

export default function VoiceAlert({ audioUrl = null, playing = false }) {
  const audioRef = useRef(null)

  useEffect(() => {
    const el = audioRef.current
    if (!el || !audioUrl) return
    if (playing) {
      el.currentTime = 0
      el.play().catch(() => {})
    }
  }, [audioUrl, playing])

  if (!audioUrl) return null

  return (
    <audio ref={audioRef} src={audioUrl} preload="metadata" className="sr-only" />
  )
}
