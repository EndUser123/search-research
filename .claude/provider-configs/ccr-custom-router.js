// ponytail: route the local Claude Code model slot to llama.cpp (run-ornith-server.ps1, port 8010).
// CCR's default router only honors opus/sonnet/haiku keywords + the six named
// role keys (default/background/think/longContext/webSearch/image), so a custom
// model name set via ANTHROPIC_CUSTOM_MODEL_OPTION would otherwise fall back to
// `default`. This custom router runs first; returning null falls through to the
// normal Router config for every other request.
//
// RESTART REQUIRED AFTER EDIT: CCR loads this module via require() at startup
// and Node caches it — config.json is hot-reloaded, but this file is NOT.
// Editing it without restarting CCR (e.g. `Stop-Process -Id <ccr-pid>; ccr start`)
// leaves the old routing in memory. Seen 2026-07-04: lmstudio->llama-cpp rename
// here didn't take effect until the gateway was restarted.
module.exports = async function router(req, config) {
  const model = req?.body?.model;
  if (model === "claude-local-ornith") {
    return "llama-cpp,ornith-1.0-9b";
  }
  return null;
};
