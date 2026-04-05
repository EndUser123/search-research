import { generateCodeTemplate } from '../src/agents/codeGenerator';

describe('Code Generator', () => {
  const npmComposition = {
    ecosystem: 'npm' as const,
    packages: [{ name: 'axios', version: '1.6.0', role: 'http', why: 'Best' }],
    compatibility_check: { status: 'compatible' as const, issues: [], warnings: [] },
    installation_command: 'npm install axios@1.6.0'
  };

  const pipComposition = {
    ecosystem: 'pip' as const,
    packages: [{ name: 'requests', version: '2.31.0', role: 'http', why: 'Best' }],
    compatibility_check: { status: 'compatible' as const, issues: [], warnings: [] },
    installation_command: 'pip install requests==2.31.0'
  };

  test('generates npm template', () => {
    const result = generateCodeTemplate(['http'], npmComposition);
    const pkgJson = JSON.parse(result.package_json);
    expect(pkgJson.dependencies).toHaveProperty('axios', '1.6.0');
    expect(result.main_code).toContain('export async function main()');
  });

  test('generates pip template', () => {
    const result = generateCodeTemplate(['http'], pipComposition);
    expect(result.requirements_txt).toContain('requests==2.31.0');
    expect(result.main_code).toContain('def main()');
    expect(result.pyproject_toml).toContain('[project]');
  });

  test('npm has tsconfig, pip does not', () => {
    const npmResult = generateCodeTemplate(['http'], npmComposition);
    const pipResult = generateCodeTemplate(['http'], pipComposition);
    expect(JSON.parse(npmResult.tsconfig)).toBeDefined();
    expect(pipResult.tsconfig).toBe('');
  });
});
