import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ToastProvider } from '@/components/ui/Toast';
import { NewReviewPage } from '@/pages/NewReviewPage';
import { reviewService } from '@/services/reviewService';
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('@/services/reviewService', () => ({
  reviewService: {
    create: vi.fn(),
    upload: vi.fn(),
    detectLanguage: vi.fn(),
  }
}));

// Mock Editor component so it doesn't try to load monaco
vi.mock('@monaco-editor/react', () => {
  return {
    default: ({ onChange }: any) => (
      <textarea
        data-testid="monaco-editor"
        onChange={(e) => onChange(e.target.value)}
      />
    )
  };
});

describe('NewReviewPage Regression Tests', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <ToastProvider><NewReviewPage /></ToastProvider>
      </MemoryRouter>
    );
  };

  it('Tabs check: Paste Code and Upload File are present, GitHub Repo is not present', () => {
    renderComponent();
    expect(screen.getByText('Paste Code')).toBeInTheDocument();
    expect(screen.getByText('Upload File')).toBeInTheDocument();
    expect(screen.queryByText('GitHub Repo')).not.toBeInTheDocument();
    expect(screen.queryByText('Repository URL')).not.toBeInTheDocument();
  });

  it('Existing Paste Code submission still works', async () => {
    (reviewService.detectLanguage as any).mockResolvedValue({ detected_language: 'Python', confidence: 99 });
    (reviewService.create as any).mockResolvedValue({ id: '123' });

    renderComponent();
    
    // Fill title
    fireEvent.change(screen.getByPlaceholderText('e.g. Authentication Module Refactor'), { target: { value: 'Test Paste' } });
    
    // Type in editor mock
    fireEvent.change(screen.getByTestId('monaco-editor'), { target: { value: 'print("Hello Paste")' } });
    
    fireEvent.click(screen.getByText('Submit for Review'));

    await waitFor(() => {
      expect(reviewService.create).toHaveBeenCalledWith(expect.objectContaining({
        title: 'Test Paste',
        source_code: 'print("Hello Paste")',
      }));
    });
  });

  it('Uploading a valid Python file creates a review successfully', async () => {
    (reviewService.detectLanguage as any).mockResolvedValue({ detected_language: 'Python', confidence: 99 });
    (reviewService.upload as any).mockResolvedValue({ id: '124' });

    renderComponent();
    
    // Switch to upload tab
    fireEvent.click(screen.getByText('Upload File'));

    // Fill title
    fireEvent.change(screen.getByPlaceholderText('e.g. Authentication Module Refactor'), { target: { value: 'Test Upload Python' } });

    // Mock dropzone upload
    const file = new File(['print("Hello Python File")'], 'test.py', { type: 'text/plain' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    Object.defineProperty(input, 'files', {
      value: [file]
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText('test.py')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Submit for Review'));

    await waitFor(() => {
      expect(reviewService.upload).toHaveBeenCalled();
      const formData = (reviewService.upload as any).mock.calls[0][0];
      const reqData = JSON.parse(formData.get('req_data'));
      
      // Uploaded code reaches /api/v1/reviews as the same source_code content as Paste Code
      expect(reqData.source_code).toBe('print("Hello Python File")');
      expect(reqData.title).toBe('Test Upload Python');
      expect(reqData.file_name).toBe('test.py');
    });
  });

  it('The same behavior works for at least one other supported language (C++)', async () => {
    (reviewService.detectLanguage as any).mockResolvedValue({ detected_language: 'C++', confidence: 99 });
    (reviewService.upload as any).mockResolvedValue({ id: '125' });

    renderComponent();
    
    // Switch to upload tab
    fireEvent.click(screen.getByText('Upload File'));

    // Fill title
    fireEvent.change(screen.getByPlaceholderText('e.g. Authentication Module Refactor'), { target: { value: 'Test Upload C++' } });

    // Mock dropzone upload
    const file = new File(['#include <iostream>\nint main() { return 0; }'], 'main.cpp', { type: 'text/plain' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    Object.defineProperty(input, 'files', {
      value: [file]
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText('main.cpp')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Submit for Review'));

    await waitFor(() => {
      expect(reviewService.upload).toHaveBeenCalled();
      const formData = (reviewService.upload as any).mock.calls[0][0];
      const reqData = JSON.parse(formData.get('req_data'));
      
      expect(reqData.source_code).toBe('#include <iostream>\nint main() { return 0; }');
      expect(reqData.title).toBe('Test Upload C++');
      expect(reqData.file_name).toBe('main.cpp');
    });
  });
});

