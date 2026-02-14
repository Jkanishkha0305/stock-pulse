/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'DM Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        pulse: {
          mint:  '#41d6ad',
          amber: '#f4bf4f',
          coral: '#ff7a66',
          ink:   '#0a1220',
          slate: '#121f33',
          cyan:  '#22d3ee',
          purple:'#a78bfa',
        },
      },
      keyframes: {
        'ping-slow': {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.8' },
          '50%':      { transform: 'scale(1.4)', opacity: '0' },
        },
        'glow-pulse': {
          '0%, 100%': { boxShadow: '0 0 8px 2px rgba(65,214,173,0.25)' },
          '50%':      { boxShadow: '0 0 20px 6px rgba(65,214,173,0.5)' },
        },
        'glow-amber': {
          '0%, 100%': { boxShadow: '0 0 8px 2px rgba(244,191,79,0.25)' },
          '50%':      { boxShadow: '0 0 20px 6px rgba(244,191,79,0.5)' },
        },
        'glow-red': {
          '0%, 100%': { boxShadow: '0 0 8px 2px rgba(255,122,102,0.3)' },
          '50%':      { boxShadow: '0 0 24px 8px rgba(255,122,102,0.6)' },
        },
        'slide-in-right': {
          '0%':   { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)',    opacity: '1' },
        },
        'slide-down': {
          '0%':   { transform: 'translateY(-100%)', opacity: '0' },
          '100%': { transform: 'translateY(0)',     opacity: '1' },
        },
        'typewriter': {
          '0%':   { width: '0' },
          '100%': { width: '100%' },
        },
        'draw-line': {
          '0%':   { strokeDashoffset: '1000' },
          '100%': { strokeDashoffset: '0' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-6px)' },
        },
      },
      animation: {
        'ping-slow':       'ping-slow 2s cubic-bezier(0,0,0.2,1) infinite',
        'glow-pulse':      'glow-pulse 2.5s ease-in-out infinite',
        'glow-amber':      'glow-amber 2.5s ease-in-out infinite',
        'glow-red':        'glow-red 1.5s ease-in-out infinite',
        'slide-in-right':  'slide-in-right 0.4s ease-out',
        'slide-down':      'slide-down 0.3s ease-out',
        'float':           'float 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
