import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#0E1A2B",
        surface: "#152238",
        surface2: "#1B2A44",
        border: "#28374F",
        primary: "#2E6F6E",
        "primary-light": "#4A9291",
        accent: "#C98A2C",
        text: "#E9EEF3",
        muted: "#8C99AC",
        success: "#3C8768",
        warning: "#C98A2C",
        high: "#C24D3D",
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "Georgia", "serif"],
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      borderRadius: {
        sm: "3px",
        DEFAULT: "4px",
        md: "6px",
      },
    },
  },
  plugins: [],
};
export default config;
