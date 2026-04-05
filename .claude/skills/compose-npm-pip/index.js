#!/usr/bin/env node
/**
 * /compose-npm-pip skill implementation
 * 
 * Generates project scaffolding from natural language prompts.
 * Uses prompt-to-workflow library for intent parsing and code generation.
 */

import { promptToWorkflow } from '../../../projects/prompt-to-workflow/src/index.js';

// Parse CLI arguments
const args = process.argv.slice(2);
let userPrompt = '';
let ecosystem = undefined; // auto-detect

// Parse arguments
for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg === '--ecosystem') {
    ecosystem = args[++i];
  } else if (arg === '--npm') {
    ecosystem = 'npm';
  } else if (arg === '--pip') {
    ecosystem = 'pip';
  } else if (!arg.startsWith('--')) {
    userPrompt += (userPrompt ? ' ' : '') + arg;
  }
}

if (!userPrompt) {
  console.error('Usage: /compose-npm-pip <prompt> [--ecosystem npm|pip]');
  process.exit(1);
}

// Run workflow
console.log('🔧 Composing project scaffold...');
promptToWorkflow(userPrompt, { ecosystem })
  .then((result) => {
    console.log('');
    console.log('## Result');
    console.log('Status:', result.status);
    
    if (result.solution) {
      console.log('');
      console.log('## Main Code');
      console.log('```' + (ecosystem === 'pip' ? 'python' : 'typescript'));
      console.log(result.solution.main_code);
      console.log('```');
      
      console.log('');
      console.log('## Dependencies');
      if (ecosystem === 'pip') {
        console.log('```text');
        console.log(result.solution.requirements_txt);
        console.log('```');
      } else {
        console.log('```json');
        console.log(result.solution.package_json);
        console.log('```');
      }
      
      console.log('');
      console.log('## Installation');
      console.log(result.solution.installation_command || 'npm install');
    }
    
    if (result.metadata.errors_encountered.length > 0) {
      console.log('');
      console.log('## Errors');
      result.metadata.errors_encountered.forEach(err => console.log('  -', err));
    }
  })
  .catch((error) => {
    console.error('Error:', error.message);
    process.exit(1);
  });
