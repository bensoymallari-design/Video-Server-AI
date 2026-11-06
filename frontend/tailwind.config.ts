import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#090b0d",
        panel: "#12161b",
        panel2: "#181e25",
        line: "#2a333c",
        amber: "#e2a23a",
        signal: "#7dcea0",
        alarm: "#e06c6c",
        mist: "#93a0ab",
        paper: "#e7eef3",
      },
      fontFamily: {
        sans: ["Segoe UI", "Helvetica Neue", "Arial", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Cascadia Code", "Menlo", "monospace"],
      },
      boxShadow: {
        inset: "inset 0 0 0 1px #2a333c",
      },
    },
  },
  plugins: [],
};

export default config;
