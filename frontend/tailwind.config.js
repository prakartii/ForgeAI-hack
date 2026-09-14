/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Audit-ledger palette: warm paper, charcoal-navy ink, and four
        // semantic accents (never decorative -- each maps to one state).
        paper: {
          DEFAULT: '#F6F6F2',
          panel: '#FCFCFA',
          sunk: '#EFEEE7',
        },
        ink: {
          DEFAULT: '#171A21',
          soft: '#4B5160',
          faint: '#8A8F9C',
        },
        line: {
          DEFAULT: '#E1DFD6',
          strong: '#CBC9BD',
        },
        ledger: {
          DEFAULT: '#1F3A5F',
          50: '#EAF0F6',
          100: '#CFDCE9',
          600: '#1F3A5F',
          700: '#182E4B',
        },
        seal: {
          DEFAULT: '#A6341E',
          50: '#F8E9E5',
          100: '#EFC9BF',
          600: '#A6341E',
          700: '#832615',
        },
        verdant: {
          DEFAULT: '#1F5C4A',
          50: '#E6F0EC',
          100: '#C2DED3',
          600: '#1F5C4A',
          700: '#164536',
        },
        brass: {
          DEFAULT: '#96631B',
          50: '#F6EEDF',
          100: '#E9D6AF',
          600: '#96631B',
          700: '#754C12',
        },
      },
      fontFamily: {
        serif: ['"IBM Plex Serif"', 'Georgia', 'serif'],
        sans: ['"IBM Plex Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
