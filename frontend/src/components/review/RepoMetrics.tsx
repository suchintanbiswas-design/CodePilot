import { Card } from '@/components/ui/Card';

interface RepoMetricsProps {
  metrics: {
    healthScore: number;
    duplicateCode: string;
    complexityHotspots: number;
    languageDistribution: Record<string, string>;
    largestFiles: string[];
  };
}

export function RepoMetrics({ metrics }: RepoMetricsProps) {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-[var(--color-text)] mb-4">Repository Analytics</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        <div className="p-4 bg-[var(--color-surface-hover)] rounded-lg border border-[var(--color-border)]">
          <div className="text-sm text-[var(--color-text-secondary)] mb-1">Health Score</div>
          <div className="text-2xl font-bold text-[var(--color-primary-500)]">{metrics.healthScore}/100</div>
        </div>

        <div className="p-4 bg-[var(--color-surface-hover)] rounded-lg border border-[var(--color-border)]">
          <div className="text-sm text-[var(--color-text-secondary)] mb-1">Duplicate Code</div>
          <div className="text-2xl font-bold text-[var(--color-text)]">{metrics.duplicateCode}</div>
        </div>

        <div className="p-4 bg-[var(--color-surface-hover)] rounded-lg border border-[var(--color-border)]">
          <div className="text-sm text-[var(--color-text-secondary)] mb-1">Complexity Hotspots</div>
          <div className="text-2xl font-bold text-[var(--color-warning-500)]">{metrics.complexityHotspots}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        <div>
          <h4 className="text-sm font-semibold text-[var(--color-text)] mb-3 border-b border-[var(--color-border)] pb-2">Language Distribution</h4>
          <ul className="space-y-2">
            {Object.entries(metrics.languageDistribution).map(([lang, pct]) => (
              <li key={lang} className="flex justify-between text-sm">
                <span className="text-[var(--color-text-secondary)]">{lang}</span>
                <span className="font-medium text-[var(--color-text)]">{pct}</span>
              </li>
            ))}
          </ul>
        </div>
        
        <div>
          <h4 className="text-sm font-semibold text-[var(--color-text)] mb-3 border-b border-[var(--color-border)] pb-2">Largest Files</h4>
          <ul className="space-y-2 text-sm text-[var(--color-text-secondary)] font-mono">
            {metrics.largestFiles.map((file, i) => (
              <li key={i} className="truncate" title={file}>
                {file}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Card>
  );
}
