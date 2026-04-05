// Main intent analysis from Claude
export type Ecosystem = 'npm' | 'pip';

export interface IntentAnalysis {
  task: string;
  requirements: string[];
  ecosystem: Ecosystem;
  constraints: {
    error_handling: boolean;
    output_format: string;
    typescript: boolean;
  };
  estimated_complexity: 'low' | 'medium' | 'high';
  problem_type: string;
}

// Package candidate from registry search (works for both npm and pip)
export interface PackageCandidate {
  name: string;
  version: string;
  description: string;
  ecosystem: Ecosystem;
  downloads_weekly: number;
  github_stars: number;
  last_update: string;
  has_types: boolean;
  maintenance_score: number;
  score: number;
  rank: number;
}

// Composition result after package selection
export interface CompositionResult {
  ecosystem: Ecosystem;
  packages: Array<{
    name: string;
    version: string;
    role: string;
    why: string;
  }>;
  compatibility_check: {
    status: 'compatible' | 'needs_review' | 'incompatible';
    issues: string[];
    warnings: string[];
  };
  installation_command: string;
}

// Generated code files
export interface GeneratedSolution {
  main_code: string;
  test_code: string;
  package_json: string;
  requirements_txt: string;
  pyproject_toml: string;
  tsconfig: string;
  build_status: 'success' | 'failed';
  test_status: 'passed' | 'failed';
  validation_errors: string[];
}

// Final workflow result
export interface WorkflowResult {
  status: 'success' | 'partial' | 'failed';
  solution: GeneratedSolution;
  packages_used: Array<{
    name: string;
    version: string;
    role: string;
    download_link: string;
  }>;
  metadata: {
    generation_time_ms: number;
    iterations_needed: number;
    errors_encountered: string[];
  };
}

// Options for workflow execution
export interface WorkflowOptions {
  ecosystem?: Ecosystem;  // Override auto-detection
  parallel?: boolean;     // Search both ecosystems (default: true)
}

// Error classification system
export enum ErrorCategory {
  MISSING_DEPENDENCY = 'missing_dependency',
  VERSION_CONFLICT = 'version_conflict',
  WRONG_API = 'wrong_api',
  TYPE_ERROR = 'type_error',
  RUNTIME_ERROR = 'runtime_error',
  TEST_FAILURE = 'test_failure',
  UNKNOWN = 'unknown'
}

export interface ErrorClassification {
  category: ErrorCategory;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  recovery_strategy: 'retry_with_alt_package' | 'fix_code' | 'abort';
}
