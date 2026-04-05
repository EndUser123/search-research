import { parseIntent } from '../src/agents/intentParser';

describe('Intent Parser', () => {
  test('detects npm ecosystem from Node keywords', async () => {
    const result = await parseIntent('Create a TypeScript API server');
    expect(result.ecosystem).toBe('npm');
  });

  test('detects pip ecosystem from Python keywords', async () => {
    const result = await parseIntent('Create a FastAPI web scraper');
    expect(result.ecosystem).toBe('pip');
  });

  test('defaults to npm when no ecosystem keywords', async () => {
    const result = await parseIntent('Make something cool');
    expect(result.ecosystem).toBe('npm');
  });

  test('respects explicit ecosystem override', async () => {
    const result = await parseIntent('Create a web scraper', { ecosystem: 'pip' });
    expect(result.ecosystem).toBe('pip');
  });

  test('extracts task from prompt', async () => {
    const result = await parseIntent('Create a web scraper');
    expect(result.task).toBe('Create a web scraper');
  });

  test('detects keywords in prompt', async () => {
    const result = await parseIntent('Build an API fetcher that scrapes data');
    expect(result.requirements).toContain('fetch');
    expect(result.requirements).toContain('scrape');
  });

  test('sets typescript true for npm ecosystem', async () => {
    const result = await parseIntent('Create an API');
    expect(result.constraints.typescript).toBe(true);
  });
});
