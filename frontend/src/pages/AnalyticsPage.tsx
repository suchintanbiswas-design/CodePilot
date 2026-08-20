import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { BarChart3, TrendingUp, AlertTriangle, CheckCircle, PieChart as PieChartIcon } from 'lucide-react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import api from '@/config/api';

const COLORS = ['#3b82f6', '#eab308', '#22c55e', '#a855f7'];

export function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  
  const [trendData, setTrendData] = useState<{name: string, quality: number, issues: number, techDebt: number}[]>([]);
  const [langData, setLangData] = useState<{name: string, value: number}[]>([]);
  const [issueTypeData, setIssueTypeData] = useState<{name: string, count: number}[]>([]);
  const [metrics, setMetrics] = useState({
    avgScore: 0,
    issuesDetected: 0,
    criticalAlerts: 0,
    reviewsRun: 0,
  });

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await api.get('/reviews/dashboard/analytics');
        const data = response.data.data;
        
        if (data.trendData) setTrendData(data.trendData);
        if (data.langData) setLangData(data.langData);
        if (data.issueTypeData) setIssueTypeData(data.issueTypeData);
        if (data.metrics) setMetrics(data.metrics);
      } catch (err) {
        console.error('Failed to fetch analytics', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <Skeleton className="h-10 w-48 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32 rounded-xl" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-[400px] rounded-xl" />
          <Skeleton className="h-[400px] rounded-xl" />
          <Skeleton className="h-[400px] rounded-xl" />
          <Skeleton className="h-[400px] rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Analytics & Insights</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">Track your code quality improvements and review patterns over time.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-[var(--color-text-secondary)]">Average Score</p>
              <h3 className="text-3xl font-bold text-[var(--color-text-primary)] mt-1">{metrics.avgScore}</h3>
            </div>
            <div className="p-2 bg-green-500/10 text-green-500 rounded-lg">
              <TrendingUp size={20} />
            </div>
          </div>
          <p className="text-xs text-green-500 font-medium">+5.2% from last month</p>
        </Card>
        
        <Card className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-[var(--color-text-secondary)]">Issues Detected</p>
              <h3 className="text-3xl font-bold text-[var(--color-text-primary)] mt-1">{metrics.issuesDetected}</h3>
            </div>
            <div className="p-2 bg-blue-500/10 text-blue-500 rounded-lg">
              <CheckCircle size={20} />
            </div>
          </div>
          <p className="text-xs text-blue-500 font-medium">+12% from last month</p>
        </Card>

        <Card className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-[var(--color-text-secondary)]">Critical Alerts</p>
              <h3 className="text-3xl font-bold text-[var(--color-text-primary)] mt-1">{metrics.criticalAlerts}</h3>
            </div>
            <div className="p-2 bg-red-500/10 text-red-500 rounded-lg">
              <AlertTriangle size={20} />
            </div>
          </div>
          <p className="text-xs text-red-500 font-medium">-2 from last month</p>
        </Card>

        <Card className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-[var(--color-text-secondary)]">Reviews Run</p>
              <h3 className="text-3xl font-bold text-[var(--color-text-primary)] mt-1">{metrics.reviewsRun}</h3>
            </div>
            <div className="p-2 bg-purple-500/10 text-purple-500 rounded-lg">
              <BarChart3 size={20} />
            </div>
          </div>
          <p className="text-xs text-purple-500 font-medium">+24 this week</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-6">Code Quality Trend</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorQuality" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="name" stroke="var(--color-text-tertiary)" tick={{ fill: 'var(--color-text-secondary)' }} />
                <YAxis stroke="var(--color-text-tertiary)" tick={{ fill: 'var(--color-text-secondary)' }} domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', borderRadius: '8px' }}
                  itemStyle={{ color: 'var(--color-text-primary)' }}
                />
                <Area type="monotone" dataKey="quality" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorQuality)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-6">Technical Debt & Issues</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="name" stroke="var(--color-text-tertiary)" tick={{ fill: 'var(--color-text-secondary)' }} />
                <YAxis stroke="var(--color-text-tertiary)" tick={{ fill: 'var(--color-text-secondary)' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', borderRadius: '8px' }}
                />
                <Legend />
                <Line type="monotone" dataKey="techDebt" name="Tech Debt Index" stroke="#eab308" strokeWidth={2} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="issues" name="Open Issues" stroke="#ef4444" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-6 flex items-center gap-2">
            <PieChartIcon size={18} className="text-[var(--color-primary-500)]" />
            Language Distribution
          </h3>
          <div className="h-[300px] w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={langData}
                  cx="50%"
                  cy="50%"
                  innerRadius={80}
                  outerRadius={110}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {langData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', borderRadius: '8px' }}
                />
                <Legend verticalAlign="bottom" height={36} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-6">Issue Distribution</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={issueTypeData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
                <XAxis type="number" stroke="var(--color-text-tertiary)" tick={{ fill: 'var(--color-text-secondary)' }} />
                <YAxis dataKey="name" type="category" stroke="var(--color-text-tertiary)" tick={{ fill: 'var(--color-text-secondary)' }} />
                <Tooltip 
                  cursor={{ fill: 'var(--color-surface-secondary)' }}
                  contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', borderRadius: '8px' }}
                />
                <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} barSize={30}>
                  {issueTypeData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={index === 0 ? '#ef4444' : index === 1 ? '#eab308' : index === 2 ? '#3b82f6' : '#22c55e'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}
