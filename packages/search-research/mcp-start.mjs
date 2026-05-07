#!/usr/bin/env node
// Wrapper for mcp-mux that resolves config from the script's own directory.
// Uses import.meta.url so it works regardless of CWD or env vars.
import { execFileSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const configPath = resolve(__dirname, '.mcp-mux.json');

const args = ['github:jasonwarta/mcp-mux', '--config', configPath];
try {
  execFileSync('npx', args, { stdio: 'inherit', env: process.env, shell: true });
} catch (e) {
  process.exit(e.status || 1);
}
