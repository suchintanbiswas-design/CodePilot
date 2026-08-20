import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { ROUTES } from '@/config/routes';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { 
  PlusCircle, Code, CheckCircle, 
  FileCode2, TrendingUp, Zap, Sparkles, FolderGit2
} from 'lucide-react';
import { Review } from '@/types/review';
import { formatDate } from '@/lib/utils';
import { reviewService } from '@/services/reviewService';

import api from '@/config/api';

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [reviews, setReviews] = useState<Review[]>([]);
  
  // Extended metrics
  const [stats, setStats] = useState({
    avgScore: 0,
    reviewStreak: 0,
    aiUsageTokens: 'N/A',
    techDebtTrend: null as number | null,
    languagesData: [] as {name: string, percent: number, color: string}[],
  });

  const formatTokens = (tokens: number | null | undefined): string => {
    if (tokens === null || tokens === undefined) return 'N/A';
    if (tokens < 1000) return tokens.toString();
    if (tokens < 1000000) return (tokens / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
    return (tokens / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
  };

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch recent reviews
        const listData = await reviewService.list({ limit: 5 });
        setReviews(listData.items || []);
        
        // Fetch real dashboard metrics
        const metricsRes = await api.get('/reviews/dashboard/metrics');
        if (metricsRes.data.success) {
          const metrics = metricsRes.data.data;
          setStats({
            avgScore: metrics.avgScore || 0,
            reviewStreak: metrics.reviewStreak || 0,
            aiUsageTokens: formatTokens(metrics.aiUsageTokens),
            techDebtTrend: metrics.techDebtTrend,
            languagesData: metrics.languages || [],
          });
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed': return <Badge variant="default" className="bg-green-500 hover:bg-green-600">Completed</Badge>;
      case 'processing': return <Badge variant="info" className="text-blue-500 border-blue-500">Processing</Badge>;
      case 'failed': return <Badge variant="error">Failed</Badge>;
      default: return <Badge variant="default">Pending</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)]">
            Welcome back, {user?.fullName?.split(' ')[0] || 'Developer'}
          </h2>
          <p className="text-[var(--color-text-secondary)] mt-1">
            Here's your code quality overview and recent activity.
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => navigate(ROUTES.HISTORY)}>
            History
          </Button>
          <Button onClick={() => navigate(ROUTES.NEW_REVIEW)} className="bg-[var(--color-primary-600)] hover:bg-[var(--color-primary-700)] text-white">
            <PlusCircle className="mr-2" size={18} />
            New Review
          </Button>
        </div>
      </div>

      {/* Extended Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex justify-between items-start mb-2">
              <p className="text-sm font-medium text-[var(--color-text-secondary)]">Average Score</p>
              <div className="p-2 bg-green-500/10 text-green-500 rounded-lg"><CheckCircle size={18} /></div>
            </div>
            {loading ? <Skeleton className="h-8 w-16" /> : (
              <div className="flex items-baseline gap-2">
                <h3 className="text-3xl font-bold text-[var(--color-text-primary)]">{stats.avgScore}</h3>
                <span className="text-xs text-green-500 font-medium">/100</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex justify-between items-start mb-2">
              <p className="text-sm font-medium text-[var(--color-text-secondary)]">Tech Debt Trend</p>
              <div className="p-2 bg-blue-500/10 text-blue-500 rounded-lg"><TrendingUp size={18} /></div>
            </div>
            {loading ? <Skeleton className="h-8 w-16" /> : (
              <div className="flex items-baseline gap-2">
                {stats.techDebtTrend !== null ? (
                  <>
                    <h3 className="text-3xl font-bold text-[var(--color-text-primary)]">{Math.abs(stats.techDebtTrend)}%</h3>
                    <span className={`text-xs font-medium ${stats.techDebtTrend > 0 ? 'text-green-500' : stats.techDebtTrend < 0 ? 'text-red-500' : 'text-blue-500'}`}>
                      {stats.techDebtTrend > 0 ? 'Reduced' : stats.techDebtTrend < 0 ? 'Increased' : 'No Change'}
                    </span>
                  </>
                ) : (
                  <h3 className="text-3xl font-bold text-[var(--color-text-primary)]">N/A</h3>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex justify-between items-start mb-2">
              <p className="text-sm font-medium text-[var(--color-text-secondary)]">Review Streak</p>
              <div className="p-2 bg-orange-500/10 text-orange-500 rounded-lg"><Zap size={18} /></div>
            </div>
            {loading ? <Skeleton className="h-8 w-16" /> : (
              <div className="flex items-baseline gap-2">
                <h3 className="text-3xl font-bold text-[var(--color-text-primary)]">{stats.reviewStreak}</h3>
                <span className="text-xs text-[var(--color-text-secondary)]">Days</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-6">
            <div className="flex justify-between items-start mb-2">
              <p className="text-sm font-medium text-[var(--color-text-secondary)]">AI Usage</p>
              <div className="p-2 bg-purple-500/10 text-purple-500 rounded-lg"><Sparkles size={18} /></div>
            </div>
            {loading ? <Skeleton className="h-8 w-16" /> : (
              <div className="flex items-baseline gap-2">
                <h3 className="text-3xl font-bold text-[var(--color-text-primary)]">{stats.aiUsageTokens}</h3>
                {stats.aiUsageTokens !== 'N/A' && <span className="text-xs text-[var(--color-text-secondary)]">Tokens</span>}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content Area - Recent Reviews */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle>Recent Reviews</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4 mt-4">
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-16 w-full rounded-xl" />
                  ))}
                </div>
              ) : reviews.length > 0 ? (
                <div className="overflow-x-auto mt-4">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-[var(--color-text-secondary)] uppercase border-b border-[var(--color-border)]">
                      <tr>
                        <th className="px-4 py-3 font-medium">Project</th>
                        <th className="px-4 py-3 font-medium">Score</th>
                        <th className="px-4 py-3 font-medium">Status</th>
                        <th className="px-4 py-3 font-medium text-right">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reviews.map((review) => (
                        <tr key={review.id} className="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-surface-secondary)]/50 transition-colors group">
                          <td className="px-4 py-4">
                            <Link to={ROUTES.REVIEW_DETAIL(review.id)} className="font-medium text-[var(--color-text-primary)] group-hover:text-[var(--color-primary-500)] block truncate max-w-[200px] transition-colors">
                              {review.title}
                            </Link>
                            <span className="text-xs text-[var(--color-text-secondary)] truncate">{review.repo_url || 'Local File'}</span>
                          </td>
                          <td className="px-4 py-4 font-medium">
                            {review.status === 'completed' && review.quality_score !== undefined ? (
                              <div className="flex items-center gap-2">
                                <div className={`h-2 w-2 rounded-full ${review.quality_score >= 80 ? 'bg-green-500' : review.quality_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`} />
                                <span>{review.quality_score}</span>
                              </div>
                            ) : (
                              <span className="text-[var(--color-text-tertiary)]">-</span>
                            )}
                          </td>
                          <td className="px-4 py-4">{getStatusBadge(review.status)}</td>
                          <td className="px-4 py-4 text-right text-[var(--color-text-secondary)] whitespace-nowrap">
                            {formatDate(review.created_at)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-16 flex flex-col items-center border-2 border-dashed border-[var(--color-border)] rounded-xl mt-4">
                  <div className="h-12 w-12 rounded-full bg-[var(--color-surface-secondary)] flex items-center justify-center text-[var(--color-text-tertiary)] mb-4">
                    <Code size={24} />
                  </div>
                  <h3 className="text-lg font-medium text-[var(--color-text-primary)]">No reviews yet</h3>
                  <p className="text-[var(--color-text-secondary)] mt-1 max-w-sm mb-6">
                    Start your first code review to get AI-powered insights.
                  </p>
                  <Button onClick={() => navigate(ROUTES.NEW_REVIEW)}>
                    Start First Review
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Area */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 mt-2">
              <Button variant="outline" className="w-full justify-start text-left font-normal" onClick={() => navigate(ROUTES.NEW_REVIEW)}>
                <FolderGit2 className="mr-3 text-[var(--color-text-secondary)]" size={16} />
                Review GitHub Repository
              </Button>
              <Button variant="outline" className="w-full justify-start text-left font-normal" onClick={() => navigate(ROUTES.NEW_REVIEW)}>
                <FileCode2 className="mr-3 text-[var(--color-text-secondary)]" size={16} />
                Analyze Local Snippet
              </Button>
              <Button variant="outline" className="w-full justify-start text-left font-normal" onClick={() => navigate(ROUTES.FAVORITES)}>
                <Sparkles className="mr-3 text-yellow-500" size={16} />
                View Favorited Reviews
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">Most Used Languages</CardTitle>
            </CardHeader>
            <CardContent className="mt-4">
              <div className="space-y-4">
                {stats.languagesData.length > 0 ? (
                  stats.languagesData.map((lang) => (
                    <div key={lang.name}>
                      <div className="flex justify-between items-center mb-1 text-sm">
                        <span className="font-medium text-[var(--color-text-primary)]">{lang.name}</span>
                        <span className="text-[var(--color-text-secondary)]">{lang.percent}%</span>
                      </div>
                      <div className="h-2 w-full bg-[var(--color-surface-secondary)] rounded-full overflow-hidden">
                        <div className={`h-full ${lang.color} rounded-full`} style={{ width: `${lang.percent}%` }} />
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-[var(--color-text-secondary)]">No language data available.</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
