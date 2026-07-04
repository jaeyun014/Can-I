import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17201c",
        mint: "#2f7d5c",
        coral: "#d9573f",
        amberSoft: "#f7b955"
      }
    }
  },
  plugins: []
};

export default config;
