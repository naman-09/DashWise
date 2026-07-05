import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Serve from root so the built app + /analysis_results.json resolve under nginx.
export default defineConfig({
  base: "/",
  plugins: [react()],
  server: { port: 5173, host: true },
  preview: { port: 4173, host: true },
});
