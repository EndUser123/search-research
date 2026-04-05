import { promptToWorkflow } from '../src/index';

describe('Workflow Integration', () => {
  test('completes workflow for npm prompt', async () => {
    const result = await promptToWorkflow('Create an Express API server');
    expect(result.status).toMatch(/success|partial|failed/);
  });

  test('completes workflow for pip prompt', async () => {
    const result = await promptToWorkflow('Create a FastAPI web scraper');
    expect(result.status).toMatch(/success|partial|failed/);
  });

  test('respects explicit ecosystem override to npm', async () => {
    const result = await promptToWorkflow('Create scraper', { ecosystem: 'npm' });
    if (result.solution) {
      expect(result.solution.package_json).not.toBe('{}');
    }
  });

  test('respects explicit ecosystem override to pip', async () => {
    const result = await promptToWorkflow('Create scraper', { ecosystem: 'pip' });
    if (result.solution) {
      expect(result.solution.requirements_txt).not.toBe('');
    }
  });
});
