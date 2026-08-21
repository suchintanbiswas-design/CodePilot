import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { describe, it, expect, vi } from 'vitest';

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { fullName: 'Test User', email: 'test@example.com', role: 'user' },
    logout: vi.fn(),
  })
}));

vi.mock('@/hooks/useTheme', () => ({
  useTheme: () => ({
    theme: 'dark',
    toggleTheme: vi.fn(),
  })
}));

describe('Header', () => {
  const renderHeader = () => {
    return render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );
  };

  it('renders correctly without global search', () => {
    renderHeader();
    
    // Check that header components render
    expect(screen.getByText('CodePilot')).toBeInTheDocument();
    
    // Check that search is removed
    expect(screen.queryByPlaceholderText('Search reviews, files, or issues...')).not.toBeInTheDocument();
  });
});
