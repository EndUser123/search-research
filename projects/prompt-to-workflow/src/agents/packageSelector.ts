import { PackageCandidate, CompositionResult, Ecosystem } from "../types";

export async function selectAndComposePackages(
  candidates: Map<string, PackageCandidate[]>,
  ecosystem: Ecosystem = "npm",
  rankToUse: number = 0
): Promise<CompositionResult> {
  console.log(`🔧 Selecting packages (${ecosystem}, rank ${rankToUse})...`);

  const selected = [];
  for (const [req, pkgs] of candidates) {
    // Filter by ecosystem
    const ecosystemPkgs = pkgs.filter(p => p.ecosystem === ecosystem);
    
    if (ecosystemPkgs.length > rankToUse) {
      selected.push({ requirement: req, package: ecosystemPkgs[rankToUse] });
    } else if (ecosystemPkgs.length > 0) {
      selected.push({ requirement: req, package: ecosystemPkgs[ecosystemPkgs.length - 1] });
    }
  }

  console.log("  Selected", selected.length, "packages");

  // Generate appropriate installation command
  const installCmd = ecosystem === "pip"
    ? "pip install " + selected.map((s) => s.package.name + "==" + s.package.version).join(" ")
    : "npm install " + selected.map((s) => s.package.name + "@" + s.package.version).join(" ");

  return {
    ecosystem,
    packages: selected.map((s) => ({
      name: s.package.name,
      version: s.package.version,
      role: s.requirement,
      why: `Best fit (score: ${s.package.score.toFixed(2)})`,
    })),
    compatibility_check: { status: "compatible", issues: [], warnings: [] },
    installation_command: installCmd,
  };
}
