import { generateAndValidate } from '../dist/agents/codeGenerator.js';
import { discoverPackages } from '../dist/agents/packageDiscover.js';

async function testLoop() {
  const packages = [
    'axios', 'cheerio', 'lodash', 'express',
    'requests', 'beautifulsoup4', 'fastapi', 'pandas'
  ];
  
  console.log('=== Testing validation pipeline with all packages ===');
  
  const results = [];
  const startTime = Date.now();
  
  for (const pkg of packages) {
    const start = Date.now();
    process.stdout.write(`Testing ${pkg}...`);
    
    try {
      const ecosystem = ['requests', 'beautifulsoup4', 'fastapi', 'pandas'].includes(pkg) ? 'pip' : 'npm';
      const candidates = await discoverPackages([pkg], ecosystem);
      const result = await generateAndValidate([pkg], candidates, ecosystem);
      
      const duration = Date.now() - start;
      const status = result.build_status === 'success' && result.test_status === 'passed' ? 'PASS' : 'FAIL';
      console.log(` ${status} (${duration}ms)`);
      
      results.push({ pkg, status, duration, error: result.validation_errors?.[0] });
    } catch (error) {
      const duration = Date.now() - start;
      console.log(` FAIL (${duration}ms) - ${error.message}`);
      results.push({ pkg, status: 'FAIL', duration, error: error.message });
    }
  }
  
  const totalDuration = Date.now() - startTime;
  const passed = results.filter(r => r.status === 'PASS').length;
  
  console.log(`
=== FINAL: ${passed}/${results.length} tests passed in ${totalDuration}ms ===`);
  
  for (const r of results) {
    if (r.status === 'FAIL') {
      console.log(`  FAIL: ${r.pkg} - ${r.error}`);
    }
  }
}

testLoop().catch(console.error);
