import { PackageCandidate } from '../src/types';
import { selectAndComposePackages } from '../src/agents/packageSelector';

describe('Package Selector', () => {
  const mockNpmCandidates: Map<string, PackageCandidate[]> = new Map([
    ['http', [
      { name: 'axios', version: '1.6.0', description: 'HTTP client', ecosystem: 'npm', downloads_weekly: 0, github_stars: 100000, last_update: '2024-01-01', has_types: true, maintenance_score: 0.9, score: 0.95, rank: 0 }
    ]]
  ]);

  const mockPipCandidates: Map<string, PackageCandidate[]> = new Map([
    ['http', [
      { name: 'requests', version: '2.31.0', description: 'HTTP library', ecosystem: 'pip', downloads_weekly: 0, github_stars: 0, last_update: '2024-01-01', has_types: false, maintenance_score: 0.9, score: 0.95, rank: 0 }
    ]]
  ]);

  test('selects npm packages', async () => {
    const result = await selectAndComposePackages(mockNpmCandidates, 'npm', 0);
    expect(result.packages[0].name).toBe('axios');
    expect(result.ecosystem).toBe('npm');
  });

  test('selects pip packages', async () => {
    const result = await selectAndComposePackages(mockPipCandidates, 'pip', 0);
    expect(result.packages[0].name).toBe('requests');
    expect(result.ecosystem).toBe('pip');
  });

  test('uses npm install command', async () => {
    const result = await selectAndComposePackages(mockNpmCandidates, 'npm', 0);
    expect(result.installation_command).toContain('npm install');
  });

  test('uses pip install command', async () => {
    const result = await selectAndComposePackages(mockPipCandidates, 'pip', 0);
    expect(result.installation_command).toContain('pip install');
  });
});
