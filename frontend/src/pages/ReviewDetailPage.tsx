import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DiffEditor, Editor } from '@monaco-editor/react';
import { Review, IssueSeverity } from '@/types/review';
import { reviewService } from '@/services/reviewService';
import { Spinner } from '@/components/ui/Spinner';
import { Button } from '@/components/ui/Button';
import { ROUTES } from '@/config/routes';
import { ScoreGauge } from '@/components/review/ScoreGauge';
import { IssueCard } from '@/components/review/IssueCard';
import { RepoMetrics } from '@/components/review/RepoMetrics';
import { Card } from '@/components/ui/Card';

export function ReviewDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [review, setReview] = useState<Review | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState<IssueSeverity | 'All'>('All');
  const diffEditorRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      if (diffEditorRef.current) {
        diffEditorRef.current.setModel(null);
      }
    };
  }, []);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    const fetchReview = async () => {
      if (!id) return;
      try {
        const data = await reviewService.getById(id);
        setReview(data);
        
        if (data.status === 'completed' || data.status === 'failed') {
          setLoading(false);
          clearInterval(interval);
        } else if (data.status === 'pending' || data.status === 'processing') {
          setLoading(true);
        }
      } catch (error) {
        console.error('Failed to fetch review', error);
        setLoading(false);
        clearInterval(interval);
      }
    };

    fetchReview();
    
    // Poll every 3 seconds if not completed
    if (loading) {
      interval = setInterval(fetchReview, 3000);
    }

    return () => clearInterval(interval);
  }, [id, loading]);

  if (!review && loading) {
    return (
      <div className="flex h-full w-full items-center justify-center p-12">
        <div className="text-center space-y-4">
          <Spinner size="lg" className="text-[var(--color-primary-500)] mx-auto" />
          <p className="text-lg text-[var(--color-text-secondary)] font-medium">Initializing Analysis...</p>
        </div>
      </div>
    );
  }

  if (review?.status === 'pending' || review?.status === 'processing') {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center p-12 space-y-6 max-w-md mx-auto">
        <Spinner size="lg" className="text-[var(--color-primary-500)]" />
        <h2 className="text-2xl font-bold text-[var(--color-text)]">Processing Review</h2>
        <div className="w-full bg-[var(--color-surface-hover)] rounded-full h-2.5 overflow-hidden">
          <div className="bg-[var(--color-primary-500)] h-2.5 rounded-full animate-[pulse_2s_ease-in-out_infinite] w-2/3"></div>
        </div>
        <p className="text-center text-[var(--color-text-secondary)]">
          CodePilot is analyzing your code for quality, performance, and security issues.
        </p>
      </div>
    );
  }

  if (!review) return null;

  const filteredIssues = (review.issues || []).filter(
    (issue) => filterSeverity === 'All' || issue.severity === filterSeverity
  );

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8 animate-in fade-in duration-300">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--color-text)]">{review.title}</h1>
          <div className="mt-2 text-sm text-[var(--color-text-secondary)] flex items-center space-x-4">
            {review.repo_url && <span>Repo: {review.repo_url}</span>}
            <span className="capitalize">Status: <span className="font-semibold text-[var(--color-success)]">{review.status}</span></span>
            <span>Language: {review.metadata?.language_detection?.final_language || review.language?.name || 'Unknown'}</span>
          </div>
        </div>
        <Button variant="outline" onClick={() => navigate(ROUTES.DASHBOARD)}>Back to Dashboard</Button>
      </div>

      {/* Scoreboard */}
      <Card className="p-6 relative overflow-hidden">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-[var(--color-text)]">Review Scoreboard</h3>
          <span className="text-xs font-mono font-medium text-[var(--color-primary-500)] bg-[var(--color-primary-500)]/10 px-2 py-1 rounded border border-[var(--color-primary-500)]/20 shadow-sm">
            Powered by CodePilot Scoring Engine
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
          <ScoreGauge value={review.metadata?.scoring_engine?.overall_quality ?? review.quality_score ?? 0} label="Overall Quality" size="lg" />
          <ScoreGauge value={review.metadata?.scoring_engine?.security_score ?? review.metadata?.security_score ?? 0} label="Security Score" size="md" />
          <ScoreGauge value={review.metadata?.scoring_engine?.performance_score ?? review.metadata?.performance_score ?? 0} label="Performance" size="md" />
          
          <div className="flex flex-col items-center justify-center space-y-2 col-span-2 md:col-span-1">
            <div className="w-24 h-24 rounded-full border-4 border-[var(--color-primary-500)] flex items-center justify-center bg-[var(--color-surface-hover)] shadow-inner">
              <span className="text-3xl font-bold text-[var(--color-text-primary)]">{review.metadata?.scoring_engine?.maintainability_grade ?? review.metadata?.maintainability_grade ?? 'N/A'}</span>
            </div>
            <span className="text-sm font-medium text-[var(--color-text-secondary)]">Maintainability</span>
          </div>

          <ScoreGauge value={review.metadata?.scoring_engine?.technical_debt_score ?? 0} label="Tech Debt Health" size="md" />
        </div>
      </Card>

      {/* Language Detection */}
      {review.metadata?.language_detection && (
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-xs font-mono font-medium text-[var(--color-primary-500)] bg-[var(--color-primary-500)]/10 px-2 py-1 rounded border border-[var(--color-primary-500)]/20">
                Language Detection
              </span>
              <span className="text-sm text-[var(--color-text-secondary)]">
                Detected: <span className="font-semibold text-[var(--color-text-primary)]">{review.metadata.language_detection.detected_language}</span>
                {' '}({review.metadata.language_detection.confidence}% confidence)
              </span>
              {review.metadata.language_detection.final_language && (
                <span className="text-sm text-[var(--color-text-secondary)]">
                  → Final: <span className="font-semibold text-[var(--color-text-primary)]">{review.metadata.language_detection.final_language}</span>
                </span>
              )}
            </div>
            {review.metadata.language_detection.language_switched && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border bg-blue-500/15 text-blue-400 border-blue-500/30">
                ↻ Auto-switched from {review.metadata.language_detection.selected_language}
              </span>
            )}
            {!review.metadata.language_detection.language_switched && review.metadata.language_detection.is_match && review.metadata.language_detection.detected_language !== 'Unknown' && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border bg-emerald-500/15 text-emerald-400 border-emerald-500/30">
                ✓ Match
              </span>
            )}
          </div>
        </Card>
      )}

      {review.repo_url && review.metadata?.repo_insights && (
        <RepoMetrics metrics={{
          healthScore: review.metadata.repo_insights.repo_health_score || 0,
          duplicateCode: 'N/A', // not available in schema
          complexityHotspots: review.metadata.cyclomatic_complexity || 0,
          languageDistribution: review.metadata.repo_insights.language_distribution || {},
          largestFiles: (review.metadata.repo_insights.largest_files || []).map(f => `${f.name} (${f.size}B)`)
        }} />
      )}

      {/* Diff Editor or Original Code */}
      {review.metadata?.ai_status === 'unavailable' ? (
        <div className="space-y-6">
          <Card className="p-6 bg-[var(--color-surface)] border-l-4 border-l-amber-500">
            <h3 className="text-lg font-semibold text-[var(--color-text)] mb-2">
              {review.metadata.ai_unavailable_reason === 'rate_limit' 
                ? 'AI Improvement Unavailable' 
                : 'AI Analysis Temporarily Unavailable'}
            </h3>
            <p className="text-[var(--color-text-secondary)]">
              Gemini is temporarily unavailable. Your syntax and static analysis results are still available.
            </p>
          </Card>
          
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-[var(--color-text)] mb-4">Original Code</h3>
            <div className="h-[400px] border border-[var(--color-border)] rounded-md overflow-hidden">
              <Editor
                height="100%"
                language={(review.metadata?.language_detection?.final_language || review.language_id || 'typescript').toLowerCase()}
                value={review.source_code || ''}
                theme="vs-dark"
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                }}
              />
            </div>
          </Card>
        </div>
      ) : (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-[var(--color-text)] mb-4">Code Diff: Original vs Improved</h3>
          <div className="h-[400px] border border-[var(--color-border)] rounded-md overflow-hidden">
            <DiffEditor
              height="100%"
              language={(review.metadata?.language_detection?.final_language || review.language_id || 'typescript').toLowerCase()}
              original={review.source_code || ''}
              modified={review.improved_code || ''}
              theme="vs-dark"
              onMount={(editor) => {
                diffEditorRef.current = editor;
              }}
              options={{
                renderSideBySide: true,
                readOnly: true,
                minimap: { enabled: false },
              }}
            />
          </div>
        </Card>
      )}

      {/* Issues List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-2xl font-bold text-[var(--color-text)]">Identified Issues ({(review.issues || []).length})</h3>
          <div className="flex space-x-2">
            {(['All', 'Critical', 'High', 'Medium', 'Low'] as const).map(sev => (
              <button
                key={sev}
                onClick={() => setFilterSeverity(sev)}
                className={`px-3 py-1 text-sm rounded-full capitalize transition-colors ${
                  filterSeverity === sev 
                    ? 'bg-[var(--color-primary-500)] text-white'
                    : 'bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary-500)]'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>

        {filteredIssues.length === 0 ? (
          <div className="text-center py-12 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg">
            <p className="text-[var(--color-text-secondary)]">No issues found for the selected severity.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredIssues.map((issue, idx) => (
              <IssueCard key={idx} issue={issue} />
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
