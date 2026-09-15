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
        // Customer portal palette (FairClaim, the consumer-facing product) --
        // deliberately distinct from the engineering console's audit-ledger
        // look above: an approachable insurtech identity, not a document.
        pcream: '#FBF9F5',
        pink: '#20241F',
        pinkfaint: '#6B7268',
        pline: '#E7E3D8',
        pteal: {
          DEFAULT: '#0E6E62',
          50: '#E4F0EE',
          100: '#BFDDD7',
          600: '#0E6E62',
          700: '#0B5850',
        },
        pcoral: {
          DEFAULT: '#D9542F',
          50: '#FBEAE3',
          100: '#F3C9B7',
          600: '#D9542F',
          700: '#B23F1F',
        },
        pamber: {
          DEFAULT: '#C98A2C',
          50: '#F9EFDD',
          100: '#EFD6A6',
          600: '#C98A2C',
          700: '#A16B1C',
        },
      },
      fontFamily: {
        serif: ['"IBM Plex Serif"', 'Georgia', 'serif'],
        sans: ['"IBM Plex Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
        portal: ['Manrope', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
