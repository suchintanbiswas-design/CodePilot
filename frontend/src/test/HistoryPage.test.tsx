import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { HistoryPage } from '@/pages/HistoryPage';
import { reviewService } from '@/services/reviewService';
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('@/services/reviewService', () => ({
  reviewService: {
    list: vi.fn(),
  }
}));

const mockReviews = [
  {
    id: '1',
    repo_url: 'github.com/user/java-repo',
    status: 'completed',
    metadata: { quality_score: 95, tech_debt: 20 },
    issues: [],
    created_at: new Date().toISOString(),
    language: { name: 'Java' },
    branch: 'main'
  },
  {
    id: '2',
    repo_url: 'github.com/user/python-repo',
    status: 'completed',
    metadata: { quality_score: 75, tech_debt: 60 },
    issues: [],
    created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    language: { name: 'Python' },
    branch: 'main'
  },
  {
    id: '3',
    repo_url: 'github.com/user/cpp-repo',
    status: 'completed',
    metadata: { quality_score: 50, tech_debt: 90 },
    issues: [],
    created_at: new Date(Date.now() - 40 * 24 * 60 * 60 * 1000).toISOString(),
    language: { name: 'C++' },
    branch: 'main'
  }
];

describe('HistoryPage Filters', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    (reviewService.list as any).mockResolvedValue({ items: mockReviews, total: 3 });
  });

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <HistoryPage />
      </MemoryRouter>
    );
  };

  it('renders all reviews initially', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument();
      expect(screen.getByText('github.com/user/python-repo')).toBeInTheDocument();
      expect(screen.getByText('github.com/user/cpp-repo')).toBeInTheDocument();
    });
  });

  it('Repository search filters matching reviews (case-insensitive)', async () => {
    renderComponent();
    await waitFor(() => expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument());
    
    const searchInput = screen.getByPlaceholderText('Search repositories...');
    fireEvent.change(searchInput, { target: { value: 'PYTHON' } });

    await waitFor(() => {
      expect(screen.queryByText('github.com/user/java-repo')).not.toBeInTheDocument();
      expect(screen.getByText('github.com/user/python-repo')).toBeInTheDocument();
      expect(screen.queryByText('github.com/user/cpp-repo')).not.toBeInTheDocument();
    });
  });

  it('Language filter works', async () => {
    renderComponent();
    await waitFor(() => expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument());
    
    fireEvent.click(screen.getByText('Filters'));
    const langSelect = screen.getByLabelText('Language');
    fireEvent.change(langSelect, { target: { value: 'Java' } });

    await waitFor(() => {
      expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument();
      expect(screen.queryByText('github.com/user/python-repo')).not.toBeInTheDocument();
    });
  });

  it('Minimum score filter works', async () => {
    renderComponent();
    await waitFor(() => expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument());
    
    fireEvent.click(screen.getByText('Filters'));
    const scoreSelect = screen.getByLabelText('Min Score');
    fireEvent.change(scoreSelect, { target: { value: '80' } });

    await waitFor(() => {
      expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument();
      expect(screen.queryByText('github.com/user/python-repo')).not.toBeInTheDocument();
      expect(screen.queryByText('github.com/user/cpp-repo')).not.toBeInTheDocument();
    });
  });

  it('Date range filter works', async () => {
    renderComponent();
    await waitFor(() => expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument());
    
    fireEvent.click(screen.getByText('Filters'));
    const dateSelect = screen.getByLabelText('Date Range');
    fireEvent.change(dateSelect, { target: { value: '7' } });

    await waitFor(() => {
      expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument();
      expect(screen.queryByText('github.com/user/python-repo')).not.toBeInTheDocument();
      expect(screen.queryByText('github.com/user/cpp-repo')).not.toBeInTheDocument();
    });
  });

  it('Tech debt filter works', async () => {
    renderComponent();
    await waitFor(() => expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument());
    
    fireEvent.click(screen.getByText('Filters'));
    const debtSelect = screen.getByLabelText('Tech Debt');
    fireEvent.change(debtSelect, { target: { value: 'High' } });

    await waitFor(() => {
      expect(screen.queryByText('github.com/user/java-repo')).not.toBeInTheDocument();
      expect(screen.getByText('github.com/user/cpp-repo')).toBeInTheDocument();
    });
  });

  it('Multiple filters combine with AND logic', async () => {
    renderComponent();
    await waitFor(() => expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument());
    
    fireEvent.click(screen.getByText('Filters'));
    fireEvent.change(screen.getByLabelText('Language'), { target: { value: 'Python' } });
    fireEvent.change(screen.getByLabelText('Tech Debt'), { target: { value: 'Medium' } });

    await waitFor(() => {
      expect(screen.queryByText('github.com/user/java-repo')).not.toBeInTheDocument();
      expect(screen.getByText('github.com/user/python-repo')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Language'), { target: { value: 'Java' } });
    await waitFor(() => {
      expect(screen.queryByText('github.com/user/python-repo')).not.toBeInTheDocument();
      expect(screen.getByText('No reviews found')).toBeInTheDocument();
    });
  });

  it('Clearing/resetting filters restores the full review list', async () => {
    renderComponent();
    await waitFor(() => expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument());
    
    fireEvent.click(screen.getByText('Filters'));
    fireEvent.change(screen.getByLabelText('Language'), { target: { value: 'Python' } });
    await waitFor(() => expect(screen.queryByText('github.com/user/java-repo')).not.toBeInTheDocument());

    fireEvent.click(screen.getByText('Reset Filters'));
    await waitFor(() => {
      expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument();
      expect(screen.getByText('github.com/user/python-repo')).toBeInTheDocument();
    });
  });

  it('Empty search/filter results display the existing empty state', async () => {
    renderComponent();
    await waitFor(() => expect(screen.getByText('github.com/user/java-repo')).toBeInTheDocument());
    
    const searchInput = screen.getByPlaceholderText('Search repositories...');
    fireEvent.change(searchInput, { target: { value: 'NON_EXISTENT_REPO_1234' } });

    await waitFor(() => {
      expect(screen.getByText('No reviews found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your search or filters.')).toBeInTheDocument();
    });
  });
});
