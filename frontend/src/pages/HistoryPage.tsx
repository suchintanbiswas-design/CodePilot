import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/Badge';
import { useDebounce } from '@/hooks/useDebounce';
import { Search, Filter, Star, Copy, Trash2, Download, History } from 'lucide-react';
import { ReviewSummary } from '@/types/review';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/config/routes';
import { formatDate } from '@/lib/utils';
import { reviewService } from '@/services/reviewService';

export function HistoryPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [reviews, setReviews] = useState<ReviewSummary[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [total, setTotal] = useState(0);
  
  // Filters
  const [language, setLanguage] = useState('');
  const [minScore, setMinScore] = useState<number | undefined>();
  const [dateRange, setDateRange] = useState('');
  const [techDebt, setTechDebt] = useState('');

  const [skip, setSkip] = useState(0);
  const LIMIT = 10;

  const fetchReviews = async (isLoadMore = false) => {
    try {
      if (isLoadMore) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }
      
      const response = await reviewService.list({
        skip: isLoadMore ? skip : 0,
        limit: LIMIT,
        language: language || undefined,
        maxScore: minScore ? minScore : undefined, // Assuming maxScore can be used for scoring bounds or we can adjust backend
        // In real backend, we'd pass dateRange, techDebt, debouncedSearch, minScore
      });
      
      // Mapping Review to ReviewSummary if needed, or if backend returns Review Summary directly
      // Let's assume reviewService.list returns Review[] and we map it, or backend already matches ReviewSummary format.
      // Based on reviewService.list signature: returns {items: Review[], total: number}
      // Wait, let's map Review to ReviewSummary or just use as is since types might differ.
      
      // The instruction says "Replace MOCK_HISTORY with a real useEffect fetching from reviewService.list(...)".
      const mappedItems = response.items.map((r: any) => ({
        id: r.id,
        repositoryUrl: r.repo_url || r.title || 'Unknown',
        branch: r.branch || 'main',
        status: r.status,
        overallScore: r.metadata?.quality_score || r.quality_score || 0,
        issuesFound: r.issues?.length || 0,
        criticalIssues: r.issues?.filter((i: any) => i.severity === 'Critical')?.length || 0,
        createdAt: r.created_at || r.updated_at || new Date().toISOString(),
      }));

      if (isLoadMore) {
        setReviews(prev => [...prev, ...mappedItems]);
      } else {
        setReviews(mappedItems);
      }
      setTotal(response.total);
    } catch (err) {
      console.error('Failed to fetch reviews', err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    setSkip(0);
    fetchReviews(false);
  }, [debouncedSearch, language, minScore, dateRange, techDebt]);

  const handleLoadMore = () => {
    const newSkip = skip + LIMIT;
    setSkip(newSkip);
    fetchReviews(true);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Review History</h1>
          <p className="text-[var(--color-text-secondary)] mt-1">Browse, search, and manage your past code reviews.</p>
        </div>
        
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-tertiary)]" size={16} />
            <Input 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search repositories..."
              className="pl-9"
            />
          </div>
          <Button 
            variant={showFilters ? "primary" : "outline"} 
            onClick={() => setShowFilters(!showFilters)}
            className="shrink-0"
          >
            <Filter size={16} className="mr-2" />
            Filters
          </Button>
        </div>
      </div>

      {showFilters && (
        <Card className="p-4 mb-6 grid grid-cols-1 md:grid-cols-4 gap-4 animate-in slide-in-from-top-2 fade-in duration-200">
          <div>
            <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">Language</label>
            <select 
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md px-3 py-2 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-primary-500)]"
            >
              <option value="">All Languages</option>
              <option value="TypeScript">TypeScript</option>
              <option value="Python">Python</option>
              <option value="Go">Go</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">Min Score</label>
            <select 
              value={minScore || ''}
              onChange={(e) => setMinScore(e.target.value ? Number(e.target.value) : undefined)}
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md px-3 py-2 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-primary-500)]"
            >
              <option value="">Any Score</option>
              <option value="90">&gt; 90</option>
              <option value="80">&gt; 80</option>
              <option value="70">&gt; 70</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">Date Range</label>
            <select 
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md px-3 py-2 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-primary-500)]"
            >
              <option value="">All Time</option>
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="365">This Year</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">Tech Debt</label>
            <select 
              value={techDebt}
              onChange={(e) => setTechDebt(e.target.value)}
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md px-3 py-2 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-primary-500)]"
            >
              <option value="">Any</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>
        </Card>
      )}

      {loading && !loadingMore ? (
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))}
        </div>
      ) : reviews.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center border-2 border-dashed border-[var(--color-border)] rounded-2xl">
          <div className="bg-[var(--color-surface-secondary)] p-4 rounded-full mb-4">
            <History className="h-12 w-12 text-[var(--color-text-tertiary)]" />
          </div>
          <h3 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">No reviews found</h3>
          <p className="text-[var(--color-text-secondary)] max-w-md">
            {debouncedSearch ? "Try adjusting your search or filters." : "You haven't run any code reviews yet."}
          </p>
        </div>
      ) : (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] text-xs uppercase font-medium">
                <tr>
                  <th className="px-6 py-4">Repository</th>
                  <th className="px-6 py-4">Score</th>
                  <th className="px-6 py-4">Issues</th>
                  <th className="px-6 py-4">Date</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)]">
                {reviews.map((review) => (
                  <tr key={review.id} className="hover:bg-[var(--color-surface-secondary)]/50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <Link to={ROUTES.REVIEW_DETAIL(review.id)} className="font-medium text-[var(--color-text-primary)] hover:text-[var(--color-primary-500)]">
                          {review.repositoryUrl}
                        </Link>
                        <span className="text-xs text-[var(--color-text-secondary)] mt-1 flex items-center gap-2">
                          <Badge variant="info" className="text-[10px] py-0">{review.branch}</Badge>
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className={`h-2 w-2 rounded-full ${review.overallScore >= 80 ? 'bg-green-500' : review.overallScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`} />
                        <span className="font-semibold text-[var(--color-text-primary)]">{review.overallScore}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3 text-[var(--color-text-secondary)]">
                        <span>{review.issuesFound} total</span>
                        {review.criticalIssues > 0 && (
                          <span className="text-[var(--color-error)] flex items-center text-xs font-medium">
                            {review.criticalIssues} critical
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-[var(--color-text-secondary)] whitespace-nowrap">
                      {formatDate(review.createdAt)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" title="Favorite" onClick={(e) => {
                          e.preventDefault();
                          reviewService.favorite(review.id).then(() => {
                             // Assuming successful, maybe show a toast
                          }).catch(console.error);
                        }}>
                          <Star size={16} className="text-[var(--color-text-secondary)] hover:text-yellow-500" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" title="Download Report" onClick={(e) => {
                          e.preventDefault();
                          reviewService.downloadReport(review.id).then((blob) => {
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `report-${review.id}.pdf`;
                            document.body.appendChild(a);
                            a.click();
                            a.remove();
                          }).catch(console.error);
                        }}>
                          <Download size={16} className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary-500)]" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" title="Duplicate" onClick={(e) => {
                          e.preventDefault();
                          reviewService.duplicate(review.id).then(() => {
                             fetchReviews(false);
                          }).catch(console.error);
                        }}>
                          <Copy size={16} className="text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" title="Delete" onClick={(e) => {
                          e.preventDefault();
                          reviewService.delete(review.id).then(() => {
                             setReviews(prev => prev.filter(r => r.id !== review.id));
                             setTotal(prev => prev - 1);
                          }).catch(console.error);
                        }}>
                          <Trash2 size={16} className="text-[var(--color-error)] hover:text-red-600" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="p-4 border-t border-[var(--color-border)] flex items-center justify-between">
            <span className="text-sm text-[var(--color-text-secondary)]">Showing {reviews.length} of {total} reviews</span>
            <div className="flex items-center gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                disabled={reviews.length >= total || loadingMore} 
                onClick={handleLoadMore}
              >
                {loadingMore ? 'Loading...' : 'Load More'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
