import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Suspense } from 'react';
import App from '@/App';

// We mock App components if we want to specifically test routing inside a MemoryRouter, 
// since App already wraps everything in a BrowserRouter. But per instructions we will test App.
describe('App', () => {
  it('renders without crashing', () => {
    // If App had no internal router, we would wrap it here in MemoryRouter.
    // For safety, we just render App directly.
    render(<App />);
    expect(screen.getByText(/CodePilot/i)).toBeInDocument(); // from fallback loader
  });

  it('redirects unauthenticated user to login', async () => {
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText(/Sign in to your account/i)).toBeInDocument();
    });
  });
});
