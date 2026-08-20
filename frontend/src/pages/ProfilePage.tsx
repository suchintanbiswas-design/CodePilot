import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Avatar } from '@/components/ui/Avatar';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Github, Linkedin, Calendar, Mail, Activity, Star, X } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import api from '@/config/api';
import { parseUtcDate } from '@/lib/utils';

interface ProfileData {
  id: string;
  email: string;
  username: string;
  fullName: string | null;
  role: string;
  bio: string | null;
  avatarUrl: string | null;
  githubProfile: string | null;
  linkedinProfile: string | null;
  preferredLanguages: string[] | null;
  createdAt: string | null;
  stats: {
    totalReviews: number;
    avgScore: number;
    reposReviewed: number;
    topLanguages: string[];
  };
  activity: Record<string, number>;
}

export function ProfilePage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    full_name: '',
    bio: '',
    github_profile: '',
    linkedin_profile: '',
  });
  const [saving, setSaving] = useState(false);

  const fetchProfile = async () => {
    try {
      const response = await api.get('/users/me/profile');
      if (response.data.success) {
        setProfile(response.data.data);
      }
    } catch (err) {
      console.error('Failed to fetch profile', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleEditOpen = () => {
    if (profile) {
      setEditForm({
        full_name: profile.fullName || '',
        bio: profile.bio || '',
        github_profile: profile.githubProfile || '',
        linkedin_profile: profile.linkedinProfile || '',
      });
    }
    setEditOpen(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/users/me/profile', editForm);
      setEditOpen(false);
      setLoading(true);
      await fetchProfile();
    } catch (err) {
      console.error('Failed to update profile', err);
    } finally {
      setSaving(false);
    }
  };

  const formatJoinDate = (iso: string | null) => {
    if (!iso) return 'Unknown';
    const d = parseUtcDate(iso);
    return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const langColors = [
    'bg-blue-600 hover:bg-blue-700',
    'bg-yellow-500 text-black hover:bg-yellow-600',
    'bg-green-600 hover:bg-green-700',
    'bg-purple-600 hover:bg-purple-700',
    'bg-cyan-600 hover:bg-cyan-700',
    'bg-rose-600 hover:bg-rose-700',
  ];

  const renderHeatmap = () => {
    if (!profile) return null;
    const activity = profile.activity || {};
    const weeks = 52;
    const days = 7;
    const grid = [];

    const now = new Date();
    // Start from 52 weeks ago, aligned to Sunday
    const startDate = new Date(now);
    startDate.setDate(startDate.getDate() - (weeks * 7) + 1);
    // Align to the start of the week (Sunday)
    startDate.setDate(startDate.getDate() - startDate.getDay());

    for (let w = 0; w < weeks; w++) {
      const weekCols = [];
      for (let d = 0; d < days; d++) {
        const cellDate = new Date(startDate);
        cellDate.setDate(startDate.getDate() + w * 7 + d);
        const dateKey = cellDate.toISOString().split('T')[0];
        const count = activity[dateKey] || 0;

        let colorClass = 'bg-[var(--color-surface-secondary)]';
        if (count === 1) colorClass = 'bg-green-900/40 dark:bg-green-900/60';
        if (count === 2) colorClass = 'bg-green-700/60 dark:bg-green-700/80';
        if (count === 3) colorClass = 'bg-green-500/80 dark:bg-green-500';
        if (count >= 4) colorClass = 'bg-green-400 dark:bg-green-400';

        weekCols.push(
          <div
            key={`${w}-${d}`}
            className={`w-3 h-3 rounded-sm ${colorClass} transition-colors hover:ring-1 hover:ring-[var(--color-text-primary)]`}
            title={`${dateKey}: ${count} review${count !== 1 ? 's' : ''}`}
          />
        );
      }
      grid.push(<div key={w} className="flex flex-col gap-1">{weekCols}</div>);
    }

    return (
      <div className="overflow-x-auto pb-4">
        <div className="flex gap-1 min-w-max">
          {grid}
        </div>
        <div className="flex justify-end items-center gap-2 mt-4 text-xs text-[var(--color-text-secondary)]">
          <span>Less</span>
          <div className="w-3 h-3 rounded-sm bg-[var(--color-surface-secondary)]"></div>
          <div className="w-3 h-3 rounded-sm bg-green-900/40 dark:bg-green-900/60"></div>
          <div className="w-3 h-3 rounded-sm bg-green-700/60 dark:bg-green-700/80"></div>
          <div className="w-3 h-3 rounded-sm bg-green-500/80 dark:bg-green-500"></div>
          <div className="w-3 h-3 rounded-sm bg-green-400 dark:bg-green-400"></div>
          <span>More</span>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        <div className="flex gap-8">
          <Skeleton className="w-32 h-32 rounded-full shrink-0" />
          <div className="space-y-4 flex-1 pt-4">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-16 w-full max-w-xl" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 pt-8">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24 rounded-xl" />)}
        </div>
        <Skeleton className="h-64 w-full rounded-xl mt-8" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Edit Profile Modal */}
      {editOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setEditOpen(false)}>
          <div className="bg-[var(--color-surface)] rounded-xl shadow-xl max-w-lg w-full p-6" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-[var(--color-text-primary)]">Edit Profile</h2>
              <button onClick={() => setEditOpen(false)} className="text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]">
                <X size={20} />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1">Full Name</label>
                <input
                  type="text"
                  value={editForm.full_name}
                  onChange={e => setEditForm(f => ({ ...f, full_name: e.target.value }))}
                  className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-secondary)] text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1">Bio</label>
                <textarea
                  value={editForm.bio}
                  onChange={e => setEditForm(f => ({ ...f, bio: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-secondary)] text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1">GitHub Profile URL</label>
                <input
                  type="text"
                  value={editForm.github_profile}
                  onChange={e => setEditForm(f => ({ ...f, github_profile: e.target.value }))}
                  className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-secondary)] text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
                  placeholder="https://github.com/username"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1">LinkedIn Profile URL</label>
                <input
                  type="text"
                  value={editForm.linkedin_profile}
                  onChange={e => setEditForm(f => ({ ...f, linkedin_profile: e.target.value }))}
                  className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-secondary)] text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
                  placeholder="https://linkedin.com/in/username"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <Button variant="outline" onClick={() => setEditOpen(false)}>Cancel</Button>
              <Button onClick={handleSave} disabled={saving}>
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col md:flex-row gap-8 mb-10">
        <div className="shrink-0">
          <Avatar
            fallback={profile?.fullName?.substring(0, 2) || user?.fullName?.substring(0, 2) || 'CP'}
            size="lg"
            className="w-32 h-32 text-3xl border-4 border-[var(--color-surface)] shadow-lg"
          />
        </div>

        <div className="flex-1">
          <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-4 mb-4">
            <div>
              <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">
                {profile?.fullName || user?.fullName || 'Not provided'}
              </h1>
              <p className="text-[var(--color-text-secondary)] text-lg capitalize">
                {profile?.role || 'User'}
              </p>
            </div>
            <Button onClick={handleEditOpen}>Edit Profile</Button>
          </div>

          <p className="text-[var(--color-text-primary)] max-w-2xl mb-6 leading-relaxed">
            {profile?.bio || 'No bio provided.'}
          </p>

          <div className="flex flex-wrap gap-4 text-sm text-[var(--color-text-secondary)] mb-6">
            <div className="flex items-center gap-1.5"><Mail size={16} /> {profile?.email || user?.email || 'Not provided'}</div>
            <div className="flex items-center gap-1.5"><Calendar size={16} /> Joined {formatJoinDate(profile?.createdAt || null)}</div>
          </div>

          <div className="flex gap-3">
            {profile?.githubProfile ? (
              <Button variant="outline" size="sm" className="gap-2" onClick={() => window.open(profile.githubProfile!, '_blank')}>
                <Github size={16} /> GitHub
              </Button>
            ) : null}
            {profile?.linkedinProfile ? (
              <Button variant="outline" size="sm" className="gap-2" onClick={() => window.open(profile.linkedinProfile!, '_blank')}>
                <Linkedin size={16} /> LinkedIn
              </Button>
            ) : null}
            {!profile?.githubProfile && !profile?.linkedinProfile && (
              <span className="text-sm text-[var(--color-text-tertiary)]">No social profiles linked. Click Edit Profile to add them.</span>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card className="p-5 flex flex-col justify-center items-center text-center">
          <div className="w-10 h-10 rounded-full bg-blue-500/10 text-blue-500 flex items-center justify-center mb-3">
            <Activity size={20} />
          </div>
          <p className="text-3xl font-bold text-[var(--color-text-primary)] mb-1">{profile?.stats.totalReviews ?? 0}</p>
          <p className="text-xs text-[var(--color-text-secondary)] uppercase font-semibold tracking-wider">Total Reviews</p>
        </Card>

        <Card className="p-5 flex flex-col justify-center items-center text-center">
          <div className="w-10 h-10 rounded-full bg-green-500/10 text-green-500 flex items-center justify-center mb-3">
            <Star size={20} />
          </div>
          <p className="text-3xl font-bold text-[var(--color-text-primary)] mb-1">{profile?.stats.avgScore ?? 0}</p>
          <p className="text-xs text-[var(--color-text-secondary)] uppercase font-semibold tracking-wider">Avg Quality Score</p>
        </Card>

        <Card className="p-5 flex flex-col justify-center items-center text-center">
          <div className="w-10 h-10 rounded-full bg-purple-500/10 text-purple-500 flex items-center justify-center mb-3">
            <Github size={20} />
          </div>
          <p className="text-3xl font-bold text-[var(--color-text-primary)] mb-1">{profile?.stats.reposReviewed ?? 0}</p>
          <p className="text-xs text-[var(--color-text-secondary)] uppercase font-semibold tracking-wider">Repos Reviewed</p>
        </Card>

        <Card className="p-5">
          <p className="text-xs text-[var(--color-text-secondary)] uppercase font-semibold tracking-wider mb-4 text-center">Top Languages</p>
          <div className="flex flex-wrap gap-2 justify-center">
            {profile?.stats.topLanguages && profile.stats.topLanguages.length > 0 ? (
              profile.stats.topLanguages.map((lang, idx) => (
                <Badge key={lang} variant="default" className={langColors[idx % langColors.length]}>{lang}</Badge>
              ))
            ) : (
              <span className="text-sm text-[var(--color-text-tertiary)]">No reviews yet</span>
            )}
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-6 flex items-center gap-2">
          <Activity className="text-[var(--color-primary-500)]" />
          Review Activity
        </h3>
        {renderHeatmap()}
      </Card>
    </div>
  );
}
