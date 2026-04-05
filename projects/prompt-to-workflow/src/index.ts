import { parseIntent } from './agents/intentParser';
import { discoverPackages } from './agents/packageDiscovery';
import { generateAndValidate } from './agents/codeGenerator';
import { WorkflowResult, WorkflowOptions } from './types';

export async function promptToWorkflow(
  userPrompt: string,
  options?: WorkflowOptions
): Promise<WorkflowResult> {
  console.log('WORKFLOW GENERATION STARTED');
  const startTime = Date.now();
  const errors: string[] = [];

  try {
    const intent = await parseIntent(userPrompt, options);
    console.log('Task:', intent.task, `(${intent.ecosystem})`);

    const ecosystem = options?.ecosystem || intent.ecosystem;
    const candidates = await discoverPackages(intent.requirements, ecosystem);
    console.log('Found candidates in', candidates.size, 'categories');

    const solution = await generateAndValidate(intent.requirements, candidates, ecosystem);

    return {
      status: solution.build_status === 'success' ? 'success' : 'partial',
      solution,
      packages_used: [],
      metadata: {
        generation_time_ms: Date.now() - startTime,
        iterations_needed: 1,
        errors_encountered: errors
      }
    };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    return {
      status: 'failed',
      solution: null as any,
      packages_used: [],
      metadata: {
        generation_time_ms: Date.now() - startTime,
        iterations_needed: 0,
        errors_encountered: [errorMsg]
      }
    };
  }
}

// Check if running as main module (works in both ESM and CommonJS/Jest)
const isMain = typeof require !== 'undefined' && require.main === module;

if (isMain) {
  // Demo: Test Python ecosystem detection
  promptToWorkflow('Create a FastAPI web scraper').then((result) => {
    console.log('Python Result Status:', result.status);
  });

  // Demo: Test NPM ecosystem with explicit override
  promptToWorkflow('Create an API server', { ecosystem: 'npm' }).then((result) => {
    console.log('NPM Result Status:', result.status);
    console.log('DONE');
  });
}

export default promptToWorkflow;
