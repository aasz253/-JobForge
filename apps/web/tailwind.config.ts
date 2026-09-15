import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: "#0B0F14", light: "#11151C", lighter: "#1A2029", lightest: "#232A34" },
        accent: { DEFAULT: "#2F81F7", soft: "#1F6FEB" },
        ember: { DEFAULT: "#F85149" },
        emerald: "#3FB950",
        success: { DEFAULT: "#3FB950", soft: "#2EA043" },
        content: { DEFAULT: "#F8FAFC", soft: "#E4E7EB" }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"]
      },
      boxShadow: {
        panel: "0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 30px rgba(0,0,0,0.35)"
      }
    }
  },
  plugins: []
};
export default config;
