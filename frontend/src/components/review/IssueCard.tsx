import { Issue } from '@/types/review';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

interface IssueCardProps {
  issue: Issue;
}

function SourceBadge({ source }: { source?: string }) {
  if (!source) return null;

  const styles: Record<string, string> = {
    'Static': 'bg-slate-500/15 text-slate-400 border-slate-500/30',
    'AI': 'bg-purple-500/15 text-purple-400 border-purple-500/30',
    'Static + AI': 'bg-gradient-to-r from-slate-500/15 to-purple-500/15 text-indigo-400 border-indigo-500/30',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border ${styles[source] || styles['Static']}`}>
      {source}
    </span>
  );
}

function ConfidenceBadge({ confidence }: { confidence?: number }) {
  if (confidence === undefined) return null;

  let level = '';
  let styles = '';

  if (confidence >= 95) {
    level = 'High';
    styles = 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
  } else if (confidence >= 80) {
    level = 'Medium-High';
    styles = 'bg-blue-500/15 text-blue-400 border-blue-500/30';
  } else if (confidence >= 60) {
    level = 'Medium';
    styles = 'bg-amber-500/15 text-amber-400 border-amber-500/30';
  } else {
    level = 'Low';
    styles = 'bg-slate-500/15 text-slate-400 border-slate-500/30';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider border ${styles}`} title={`${level} Confidence`}>
      Confidence: {confidence}%
    </span>
  );
}

export function IssueCard({ issue }: IssueCardProps) {
  const getSeverityVariant = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'error';
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  return (
    <Card className="p-4 hover:border-[var(--color-primary-400)] transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Badge variant={getSeverityVariant(issue.severity) as any}>
            {issue.severity.toUpperCase()}
          </Badge>
          <SourceBadge source={issue.source} />
          <ConfidenceBadge confidence={issue.confidence} />
          {issue.file && (
            <span className="text-sm font-medium text-[var(--color-text)]">
              {issue.file}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {issue.issue_id && (
            <span className="text-[10px] font-mono text-[var(--color-text-tertiary)] bg-[var(--color-surface-hover)] px-1.5 py-0.5 rounded">
              {issue.issue_id}
            </span>
          )}
          {issue.line_number > 0 && (
            <span className="text-sm text-[var(--color-text-tertiary)] font-mono bg-[var(--color-surface-hover)] px-2 py-1 rounded">
              Line: {issue.line_number}
            </span>
          )}
        </div>
      </div>
      
      <h4 className="text-base font-semibold text-[var(--color-text)] mb-2">
        {issue.rule_type}
      </h4>
      
      <div className="space-y-3">
        <div>
          <p className="text-sm text-[var(--color-text-secondary)]">
            <span className="font-semibold text-[var(--color-text)] mr-2">Description:</span>
            {issue.description}
          </p>
          {issue.ai_explanation && (
            <p className="text-sm text-[var(--color-text-secondary)] mt-2">
              <span className="font-semibold text-[var(--color-text)] mr-2">AI Explanation:</span>
              {issue.ai_explanation}
            </p>
          )}
        </div>
        
        {issue.suggestion && (
          <div className="bg-[var(--color-surface-hover)] p-3 rounded-md border border-[var(--color-border)]">
            <span className="block text-xs font-semibold text-[var(--color-primary-500)] mb-1 uppercase tracking-wider">Suggested Fix</span>
            <pre className="text-sm text-[var(--color-text-secondary)] font-mono whitespace-pre-wrap">
              {issue.suggestion}
            </pre>
          </div>
        )}
      </div>
    </Card>
  );
}

