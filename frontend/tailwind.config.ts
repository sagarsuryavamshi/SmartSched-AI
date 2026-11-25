import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F8FAFC", // soft off-white slate-50
        surface: "#FFFFFF",
        primary: {
          DEFAULT: "#1D4ED8", // blue-700
          hover: "#1E40AF",   // blue-800
          subtle: "#EFF6FF",  // blue-50
        },
        navy: {
          900: "#0F172A",     // slate-900 (deep university navy)
          800: "#1E293B",     // slate-800
          700: "#334155",     // slate-700
          600: "#475569",     // slate-600
        },
        accent: {
          purple: "#7C3AED",  // purple-600 (lab sessions / AI highlights)
          "purple-light": "#F5F3FF",
        },
        success: {
          DEFAULT: "#15803D", // green-700
          subtle: "#F0FDF4",  // green-50
        },
        warning: {
          DEFAULT: "#B45309", // amber-700
          subtle: "#FFFBEB",  // amber-50
        },
        danger: {
          DEFAULT: "#B91C1C", // red-700
          subtle: "#FEF2F2",  // red-50
        },
        border: "#E2E8F0",    // slate-200
        muted: "#64748B",     // slate-500
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)",
        "card-hover": "0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05)",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
