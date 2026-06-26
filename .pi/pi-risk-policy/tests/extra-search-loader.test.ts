import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync, writeFileSync } from "node:fs";

// Mirror the loader so we can test it in isolation.
function loadDotEnv(path: string): void {
  if (!existsSync(path)) return;
  const content = readFileSync(path, "utf8");
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const m = line.match(/^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$/);
    if (!m) continue;
    let value = m[2];
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (!process.env[m[1]]) process.env[m[1]] = value;
  }
}

describe("extra-search env loader (P:/.env)", () => {
  it("strips surrounding quotes from values", () => {
    const tmpFile = "/tmp/test-quoted.env";
    writeFileSync(tmpFile, 'TEST_KEY="hello-world"\nTEST_SINGLE=\'single-quoted\'\nTEST_BARE=bare\n');
    delete process.env.TEST_KEY;
    delete process.env.TEST_SINGLE;
    delete process.env.TEST_BARE;
    loadDotEnv(tmpFile);
    assert.equal(process.env.TEST_KEY, "hello-world", "double quotes stripped");
    assert.equal(process.env.TEST_SINGLE, "single-quoted", "single quotes stripped");
    assert.equal(process.env.TEST_BARE, "bare", "bare value unchanged");
  });

  it("loads the actual new BRAVE_API_KEY from P:/.env (proves registry was stale)", () => {
    delete process.env.BRAVE_API_KEY;
    loadDotEnv("P:/.env");
    const key = process.env.BRAVE_API_KEY ?? "";
    assert.ok(key.length > 0, "BRAVE_API_KEY should be loaded");
    assert.ok(key.startsWith("BSA51W"), "matches the NEW key, not the OLD registry value");
  });

  it("does not overwrite existing process.env values (registry wins over .env)", () => {
    process.env.PI_ENV_TEST_OVERRIDE = "from-process-env";
    const tmpFile = "/tmp/test-env-override.env";
    writeFileSync(tmpFile, "PI_ENV_TEST_OVERRIDE=from-dotenv\n");
    loadDotEnv(tmpFile);
    assert.equal(process.env.PI_ENV_TEST_OVERRIDE, "from-process-env");
    delete process.env.PI_ENV_TEST_OVERRIDE;
  });

  it("skips comments and blank lines", () => {
    const tmpFile = "/tmp/test-env-comments.env";
    writeFileSync(
      tmpFile,
      "# this is a comment\n\nVALID_KEY=hello\n  # indented comment\nANOTHER=world\n",
    );
    delete process.env.VALID_KEY;
    delete process.env.ANOTHER;
    loadDotEnv(tmpFile);
    assert.equal(process.env.VALID_KEY, "hello");
    assert.equal(process.env.ANOTHER, "world");
  });

  it("returns silently when the file does not exist", () => {
    delete process.env.DEFINITELY_NOT_THERE;
    loadDotEnv("/tmp/this-file-does-not-exist-" + Date.now());
    assert.equal(process.env.DEFINITELY_NOT_THERE, undefined);
  });

  it("loads Tavily and Gemini too (the keys the extension needs)", () => {
    delete process.env.TAVILY_API_KEY;
    delete process.env.GEMINI_API_KEY;
    loadDotEnv("P:/.env");
    assert.ok(process.env.TAVILY_API_KEY, "TAVILY_API_KEY loaded");
    assert.ok(process.env.GEMINI_API_KEY, "GEMINI_API_KEY loaded");
  });
});

// Now actually call Brave through the loader-augmented env
describe("brave_search through P:/.env loader (end-to-end)", () => {
  it("returns 200 with real results using the key from P:/.env", async () => {
    delete process.env.BRAVE_API_KEY;
    loadDotEnv("P:/.env");
    const apiKey = process.env.BRAVE_API_KEY;
    assert.ok(apiKey, "key loaded");

    const url = new URL("https://api.search.brave.com/res/v1/web/search");
    url.searchParams.set("q", "pi coding agent extensions");
    url.searchParams.set("count", "3");
    const res = await fetch(url, {
      headers: {
        Accept: "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": apiKey,
      },
    });
    assert.equal(String(res.status), "200");
    const data = (await res.json()) as { web?: { results?: Array<{ title?: string; url?: string }> } };
    const titles = (data.web?.results ?? []).map((r) => r.title ?? "");
    assert.ok(titles.length > 0, "Brave returned at least one result");
    assert.ok(titles.some((t) => t.includes("Pi") || t.includes("pi")), "result is Pi-related");
  });
});
