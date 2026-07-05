/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      // Colors are wired to CSS custom properties (see src/index.css) so the
      // whole palette swaps for light/dark in one place. Values come from the
      // dataviz skill's validated reference palette.
      colors: {
        page: "var(--page)",
        surface: "var(--surface-1)",
        ink: "var(--text-primary)",
        "ink-secondary": "var(--text-secondary)",
        "ink-muted": "var(--text-muted)",
        line: "var(--gridline)",
        baseline: "var(--baseline)",
        series: "var(--series-1)",
        good: "var(--status-good)",
        warning: "var(--status-warning)",
        serious: "var(--status-serious)",
        critical: "var(--status-critical)",
      },
      borderColor: {
        DEFAULT: "var(--border)",
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', '"Segoe UI"', "sans-serif"],
      },
    },
  },
  plugins: [],
};
