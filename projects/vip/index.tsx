/* @refresh reload */
import { render } from 'solid-js/web';
import App from './App';

console.log('Starting SolidJS app mount...');
const root = document.getElementById('root');

if (import.meta.env.DEV && !(root instanceof HTMLElement)) {
  throw new Error(
    'Root element not found. Did you forget to add it to your index.html? Or maybe the id attribute got misspelled?',
  );
}

try {
  render(() => <App />, root!);
  console.log('SolidJS app mounted successfully.');
} catch (e) {
  console.error('Failed to mount SolidJS app:', e);
}
