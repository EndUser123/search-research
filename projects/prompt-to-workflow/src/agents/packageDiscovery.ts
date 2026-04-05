import { PackageCandidate, Ecosystem } from "../types";

interface NpmSearchResult {
  package: { name: string; version: string; description: string; };
  score: { final: number; detail: { maintenance?: number } };
  github?: { starsCount?: number };
}

interface NpmSearchResponse {
  results: NpmSearchResult[];
}

interface PyPIPackageInfo {
  info: {
    name: string;
    version: string;
    summary: string;
    author: string;
    requires_python?: string;
    upload_time?: string;
  };
  urls: Array<{
    packagetype: string;
    url: string;
  }>;
  releases: Record<string, Array<{ filename: string; packagetype: string }>>;
}

// Search PyPI for packages
async function searchPyPI(query: string): Promise<PackageCandidate[]> {
  const candidates: PackageCandidate[] = [];

  try {
    const commonPackages: Record<string, string[]> = {
      "http": ["requests", "httpx", "aiohttp"],
      "api": ["fastapi", "flask", "requests"],
      "scrape": ["beautifulsoup4", "scrapy", "selenium"],
      "parse": ["lxml", "html5lib", "pyyaml"],
      "json": ["orjson", "ujson", "jsonschema"],
      "csv": ["pandas", "csv"],
      "database": ["sqlalchemy", "pymongo", "psycopg2"],
      "validate": ["pydantic", "jsonschema", "validators"],
      "transform": ["pandas", "numpy"],
      "general": ["click", "rich", "python-dotenv"],
    };

    const packageNames = commonPackages[query.toLowerCase()] || [query];

    for (const [index, pkgName] of packageNames.entries()) {
      try {
        const url = `https://pypi.org/pypi/${pkgName}/json`;
        const response = await fetch(url);

        if (!response.ok) continue;

        const data = await response.json() as PyPIPackageInfo;
        const info = data.info;

        candidates.push({
          name: info.name,
          version: info.version,
          description: info.summary || "",
          ecosystem: "pip",
          downloads_weekly: 0,
          github_stars: 0,
          last_update: info.upload_time || new Date().toISOString(),
          has_types: false,
          maintenance_score: 0.8,
          score: 1 - (index * 0.1),
          rank: index,
        });
      } catch {
        // Skip failed lookups
      }
    }
  } catch (error) {
    console.error("PyPI search failed:", error);
  }

  return candidates;
}

// Search npm for packages
async function searchNPM(query: string): Promise<PackageCandidate[]> {
  const candidates: PackageCandidate[] = [];

  try {
    const url = `https://api.npms.io/v2/search?q=${encodeURIComponent(query)}&size=5`;
    const response = await fetch(url);

    if (!response.ok) throw new Error(`npm API returned ${response.status}`);

    const data = await response.json() as NpmSearchResponse;

    for (const [index, result] of data.results.entries()) {
      const pkg = result.package;
      candidates.push({
        name: pkg.name,
        version: pkg.version,
        description: pkg.description || "",
        ecosystem: "npm",
        downloads_weekly: 0,
        github_stars: result.github?.starsCount || 0,
        last_update: new Date().toISOString(),
        has_types: pkg.name.includes("types") || pkg.name.includes("typescript"),
        maintenance_score: result.score.detail.maintenance || 0.5,
        score: result.score.final,
        rank: index,
      });
    }
  } catch (error) {
    console.error("npm search failed:", error);
  }

  return candidates;
}

// Search packages by ecosystem
export async function discoverPackages(
  requirements: string[],
  ecosystem: Ecosystem = "npm"
): Promise<Map<string, PackageCandidate[]>> {
  const results = new Map<string, PackageCandidate[]>();
  console.log(`📦 Discovering packages for ${requirements.length} requirements (${ecosystem} mode)...`);

  for (const requirement of requirements) {
    console.log("  → Searching for:", requirement);

    let candidates: PackageCandidate[] = [];

    if (ecosystem === "pip") {
      candidates = await searchPyPI(requirement);
    } else {
      candidates = await searchNPM(requirement);
    }

    results.set(requirement, candidates);
    console.log(`    ✓ Found ${candidates.length} packages`);
  }

  return results;
}

// Search both ecosystems in parallel (for "both" mode)
export async function discoverPackagesBoth(
  requirements: string[]
): Promise<Map<string, PackageCandidate[]>> {
  const results = new Map<string, PackageCandidate[]>();
  console.log(`📦 Discovering packages for ${requirements.length} requirements (both ecosystems)...`);

  for (const requirement of requirements) {
    console.log("  → Searching for:", requirement);

    const [npmResults, pipResults] = await Promise.all([
      searchNPM(requirement),
      searchPyPI(requirement),
    ]);

    const candidates = [...npmResults, ...pipResults];
    results.set(requirement, candidates);
    console.log(`    ✓ Found ${candidates.length} packages (${npmResults.length} npm, ${pipResults.length} pip)`);
  }

  return results;
}
