/**
 * yt-workspace WXT configuration.
 *
 * Reconstructed from scratch — NOT wholesale-inherited from steipete/summarize.
 * The Summarize wxt.config.ts requests sidePanel, offscreen, webNavigation,
 * webRequest, debugger, nativeMessaging, userScripts, and <all_urls>.
 * This extension uses NONE of those. Only the minimum-permission set is here.
 *
 * Every permission must have a documented chain:
 *   permission → calling module → runtime capability → acceptance test
 * See the vertical-slice handoff "Minimum permissions" table.
 */
import { defineConfig } from "wxt";

export default defineConfig({
  srcDir: "src",
  manifestVersion: 3,
  manifest: {
    name: "YT Workspace",
    description: "YouTube workspace sidebar — Chapters, Overview, Ask, Transcript, Links",
    version: "0.1.0",
    permissions: [
      "scripting",
      "activeTab",
      "storage",
    ],
    host_permissions: [
      "*://*.youtube.com/*",
    ],
    action: {
      default_title: "Toggle YT Workspace",
    },
    background: {
      type: "module",
      service_worker: "background.js",
    },
    content_scripts: [],
    minimum_chrome_version: "120",
  },
});
