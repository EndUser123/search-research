import React from 'react';
import { render, screen } from '@testing-library/react';
import ExampleComponent from './ExampleComponent';

describe('ExampleComponent', () => {
  test('renders Hello World', () => {
    render(<ExampleComponent />);
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });
});
