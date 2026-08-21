import { render, screen, waitFor } from '@testing-library/react';
import App from '@/App';
import { describe, it, expect } from 'vitest';

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
    expect(screen.getByText(/CodePilot/i)).toBeInTheDocument();
  });

  it('redirects unauthenticated user to login', async () => {
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText(/Sign in to your account/i)).toBeInTheDocument();
    });
  });
});
