import { IntentAnalysis, Ecosystem, WorkflowOptions } from "../types";

// Python/Flask/Django/FastAPI ecosystem indicators
const PYTHON_KEYWORDS = [
  "python", "django", "flask", "fastapi", "pandas", "numpy",
  "requests", "asyncio", "pytest", "pip", "virtualenv", "poetry",
  "jupyter", "scrapy", "selenium", "celery", "sqlalchemy"
];

// Node/TypeScript ecosystem indicators
const NODE_KEYWORDS = [
  "node", "node.js", "npm", "typescript", "javascript", "ts",
  "react", "vue", "angular", "next", "nuxt", "express", "nestjs",
  "deno", "bun", "vite", "webpack"
];

function detectEcosystem(prompt: string, options?: WorkflowOptions): Ecosystem {
  // Explicit override takes precedence
  if (options?.ecosystem) {
    return options.ecosystem;
  }

  const lowerPrompt = prompt.toLowerCase();

  // Count matches for each ecosystem
  const pythonMatches = PYTHON_KEYWORDS.filter(k => lowerPrompt.includes(k)).length;
  const nodeMatches = NODE_KEYWORDS.filter(k => lowerPrompt.includes(k)).length;

  // Default to npm if no clear signal
  if (pythonMatches === 0 && nodeMatches === 0) {
    return "npm";
  }

  // Return the ecosystem with more matches
  return pythonMatches >= nodeMatches ? "pip" : "npm";
}

export async function parseIntent(prompt: string, options?: WorkflowOptions): Promise<IntentAnalysis> {
  console.log("🔍 Parsing user intent...");

  const ecosystem = detectEcosystem(prompt, options);

  // Extract task from prompt
  const task = prompt.split(".")[0].trim() || prompt;

  // Extract requirements (keyword matching)
  const requirements: string[] = [];
  const keywords = ["fetch", "parse", "api", "http", "json", "csv", "database", "scrape", "validate", "transform"];
  keywords.forEach(k => { if (prompt.toLowerCase().includes(k)) requirements.push(k); });

  if (requirements.length === 0) requirements.push("general");

  const result: IntentAnalysis = {
    task,
    requirements,
    ecosystem,
    constraints: {
      error_handling: true,
      output_format: prompt.includes("json") ? "json" : "other",
      typescript: ecosystem === "npm",
    },
    estimated_complexity: requirements.length > 3 ? "high" : requirements.length > 1 ? "medium" : "low",
    problem_type: "automation",
  };

  console.log(`✓ Parsed intent: ${result.task} (${ecosystem})`);
  return result;
}
