import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { reviewService } from '@/services/reviewService';
import { ROUTES } from '@/config/routes';
import { useToast } from '@/components/ui/Toast';

export function NewReviewPage() {
  const [activeTab, setActiveTab] = useState<'paste' | 'upload'>('paste');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { error, success } = useToast();

  // Shared state
  const [title, setTitle] = useState('');
  const [language, setLanguage] = useState(''); // Default to empty
  const [showLanguageFallback, setShowLanguageFallback] = useState(false);

  // Paste state
  const [code, setCode] = useState('// Paste your code here');

  // Upload state
  const [file, setFile] = useState<File | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, maxFiles: 1 });

  const doSubmit = async (finalLanguage: string) => {
    setIsLoading(true);
    try {
      let response;
      if (activeTab === 'paste') {
        response = await reviewService.create({
          title,
          language_id: finalLanguage || undefined, // undefined sends as omitted
          source_code: code
        });
      } else if (activeTab === 'upload') {
        if (!file) {
          error('File is required');
          setIsLoading(false);
          return;
        }
        const fileContent = await file.text();
        const formData = new FormData();
        const reqData: any = { 
          title,
          source_code: fileContent,
          file_name: file.name,
          file_size: file.size
        };
        if (finalLanguage) {
          reqData.language_id = finalLanguage;
        }
        formData.append('req_data', JSON.stringify(reqData));
        formData.append('file', file);
        response = await reviewService.upload(formData);
      }

      if (response && response.id) {
        navigate(ROUTES.REVIEW_DETAIL(response.id));
        success('Review created successfully');
      }
    } catch (err) {
      console.error(err);
      error('Failed to create review');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePreflightAndSubmit = async () => {
    if (!title) {
      error('Title is required');
      return;
    }

    // If user already selected a language from the fallback dropdown, just submit
    if (language) {
      await doSubmit(language);
      return;
    }

    // Pre-flight language detection
    try {
      let codeToDetect = '';
      let filename = undefined;
      
      if (activeTab === 'paste') {
        if (!code || !code.trim() || code === '// Paste your code here') {
          error('Code is required');
          return;
        }
        codeToDetect = code;
      } else if (activeTab === 'upload' && file) {
        codeToDetect = await file.text();
        filename = file.name;
      }

      const detection = await reviewService.detectLanguage(codeToDetect, 'Unknown', filename);
      
      if (detection.detected_language === 'Unknown' || detection.confidence < 25) {
        // Fallback required
        setShowLanguageFallback(true);
        error('Could not confidently determine the programming language. Please select a language to continue.');
        return;
      }

      // Detection confident enough, let the backend authoritative resolution handle it
      // Send without language_id
      await doSubmit('');
    } catch (err) {
      // If detection pre-flight fails completely, require manual selection
      setShowLanguageFallback(true);
      error('Language detection failed. Please select a language manually.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text)]">New Code Review</h1>
        <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
          Submit your code for AI-powered review and analysis. CodePilot will automatically detect the programming language.
        </p>
      </div>

      <Card className="p-6">
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-2">Review Title</label>
            <Input 
              placeholder="e.g. Authentication Module Refactor" 
              value={title} 
              onChange={(e) => setTitle(e.target.value)} 
            />
          </div>

          {showLanguageFallback && (
            <div className="p-4 rounded-md border border-amber-500/40 bg-amber-500/10 mb-4">
              <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
                Fallback Language Selection <span className="text-red-400">*</span>
              </label>
              <select 
                className="mt-1 block w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] py-2 pl-3 pr-10 text-base focus:border-[var(--color-primary-500)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary-500)] sm:text-sm"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="" disabled>Select a language...</option>
                <option value="Python">Python</option>
                <option value="Java">Java</option>
                <option value="C">C</option>
                <option value="C++">C++</option>
                <option value="JavaScript">JavaScript</option>
                <option value="TypeScript">TypeScript</option>
              </select>
              <p className="mt-2 text-sm text-amber-500/90">
                We couldn't confidently determine the programming language. Please select a language to continue.
              </p>
            </div>
          )}

          <div className="border-b border-[var(--color-border)]">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              {['paste', 'upload'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => {
                    setActiveTab(tab as any);
                    setShowLanguageFallback(false);
                    setLanguage('');
                  }}
                  className={`
                    whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
                    ${activeTab === tab
                      ? 'border-[var(--color-primary-500)] text-[var(--color-primary-600)] dark:text-[var(--color-primary-400)]'
                      : 'border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:border-[var(--color-border-hover)]'
                    }
                  `}
                >
                  {tab === 'paste' ? 'Paste Code' : 'Upload File'}
                </button>
              ))}
            </nav>
          </div>

          <div className="mt-6">
            {activeTab === 'paste' && (
              <div className="h-[400px] rounded-md overflow-hidden border border-[var(--color-border)]">
                <Editor
                  height="100%"
                  language={language ? language.toLowerCase() : 'plaintext'}
                  theme="vs-dark"
                  value={code}
                  onChange={(val) => setCode(val || '')}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    padding: { top: 16 }
                  }}
                />
              </div>
            )}

            {activeTab === 'upload' && (
              <div 
                {...getRootProps()} 
                className={`
                  mt-2 flex justify-center rounded-lg border-2 border-dashed px-6 py-24 transition-colors cursor-pointer
                  ${isDragActive 
                    ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-500)]/10' 
                    : 'border-[var(--color-border)] hover:border-[var(--color-primary-400)] bg-[var(--color-surface)]'
                  }
                `}
              >
                <input {...getInputProps()} />
                <div className="text-center">
                  <div className="mt-4 flex text-sm leading-6 text-[var(--color-text-secondary)]">
                    <span className="relative cursor-pointer rounded-md font-semibold text-[var(--color-primary-500)] focus-within:outline-none hover:text-[var(--color-primary-400)]">
                      {file ? file.name : 'Upload a file'}
                    </span>
                    <p className="pl-1">or drag and drop</p>
                  </div>
                  <p className="text-xs leading-5 text-[var(--color-text-tertiary)] mt-2">
                    Code files up to 2MB
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end pt-6">
            <Button onClick={handlePreflightAndSubmit} isLoading={isLoading}>
              Submit for Review
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
