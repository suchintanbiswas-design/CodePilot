import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FolderHeart, Star, Trash2, ArrowLeft, Edit2, FolderInput } from 'lucide-react';
import { Skeleton } from '@/components/ui/Skeleton';
import { ReviewSummary } from '@/types/review';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/config/routes';
import { favoriteService, Collection } from '@/services/favoriteService';

export function FavoritesPage() {
  const [loading, setLoading] = useState(true);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);
  const [reviews, setReviews] = useState<ReviewSummary[]>([]);
  const [editingCollectionId, setEditingCollectionId] = useState<string | null>(null);
  const [newCollectionName, setNewCollectionName] = useState('');

  useEffect(() => {
    fetchCollections();
  }, []);

  const fetchCollections = async () => {
    try {
      setLoading(true);
      const data = await favoriteService.getCollections();
      setCollections(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCollection = async (collection: Collection) => {
    setSelectedCollection(collection);
    fetchCollectionReviews(collection.id);
  };

  const fetchCollectionReviews = async (id: string) => {
    try {
      setLoading(true);
      const data = await favoriteService.getCollectionReviews(id);
      setReviews(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setSelectedCollection(null);
    fetchCollections();
  };

  const handleCreateCollection = async () => {
    const name = prompt("Enter new collection name:");
    if (!name) return;
    try {
      await favoriteService.createCollection(name, 'bg-blue-500');
      fetchCollections();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteCollection = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!window.confirm("Delete this collection?")) return;
    try {
      await favoriteService.deleteCollection(id);
      fetchCollections();
    } catch (err) {
      console.error(err);
    }
  };

  const handleRenameCollection = async (e: React.MouseEvent, id: string, oldName: string) => {
    e.stopPropagation();
    setEditingCollectionId(id);
    setNewCollectionName(oldName);
  };

  const handleSaveRename = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await favoriteService.updateCollection(id, newCollectionName);
      setEditingCollectionId(null);
      fetchCollections();
    } catch (err) {
      console.error(err);
    }
  };

  const handleMoveReview = async (reviewId: string, toCollectionId: string) => {
    if (!selectedCollection) return;
    try {
      await favoriteService.moveReview(reviewId, selectedCollection.id, toCollectionId);
      fetchCollectionReviews(selectedCollection.id);
    } catch (err) {
      console.error(err);
    }
  };
  
  const handleRemoveReview = async (reviewId: string) => {
    if (!selectedCollection) return;
    try {
      await favoriteService.removeReview(reviewId, selectedCollection.id);
      fetchCollectionReviews(selectedCollection.id);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-8 w-48 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (selectedCollection) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-4 mb-8">
          <Button variant="outline" size="sm" onClick={handleBack} className="rounded-full h-8 w-8 p-0">
            <ArrowLeft size={16} />
          </Button>
          <div>
            <h2 className="text-2xl font-bold text-[var(--color-text-primary)] flex items-center gap-2">
              <FolderHeart className="text-[var(--color-primary-500)]" />
              {selectedCollection.name}
            </h2>
            <p className="text-[var(--color-text-secondary)] text-sm">{selectedCollection.count} saved reviews</p>
          </div>
        </div>

        {reviews.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="bg-[var(--color-surface-secondary)] p-4 rounded-full mb-4">
              <Star className="h-12 w-12 text-[var(--color-text-tertiary)]" />
            </div>
            <h3 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">No favorites yet</h3>
            <p className="text-[var(--color-text-secondary)] max-w-md">
              You haven't added any reviews to this collection yet.
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
            {reviews.map((review) => (
              <Card key={review.id} className="p-4 flex items-center justify-between hover:border-[var(--color-primary-500)] transition-colors group">
                <div>
                  <Link to={ROUTES.REVIEW_DETAIL(review.id)} className="font-medium text-[var(--color-text-primary)] hover:underline">
                    {review.repositoryUrl.split('/').slice(-2).join('/')}
                  </Link>
                  <div className="text-sm text-[var(--color-text-secondary)] mt-1 flex items-center gap-3">
                    <span>Score: {review.overallScore}/100</span>
                    <span>•</span>
                    <span>{review.issuesFound} issues</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="relative group/dropdown">
                    <Button variant="outline" size="sm" className="gap-2">
                      <FolderInput size={14} /> Move To
                    </Button>
                    <div className="absolute right-0 top-full mt-1 hidden group-hover/dropdown:block bg-white dark:bg-gray-800 border rounded shadow-lg z-10 w-48">
                      {collections.filter(c => c.id !== selectedCollection.id).map(c => (
                        <button key={c.id} onClick={() => handleMoveReview(review.id, c.id)} className="block w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm">
                          {c.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  <Button variant="outline" size="sm" onClick={() => handleRemoveReview(review.id)} className="text-[var(--color-error)] hover:bg-[var(--color-error)]/10 hover:border-transparent">
                    <Trash2 size={14} className="mr-2"/>
                    Remove
                  </Button>
                  <Link to={ROUTES.REVIEW_DETAIL(review.id)}>
                    <Button size="sm">View Review</Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Favorites</h1>
          <p className="text-[var(--color-text-secondary)] mt-1">Organize your most valuable code reviews.</p>
        </div>
        <Button onClick={handleCreateCollection}>
          <FolderHeart size={16} className="mr-2" />
          New Collection
        </Button>
      </div>

      {collections.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center border-2 border-dashed border-[var(--color-border)] rounded-2xl">
          <div className="bg-[var(--color-surface-secondary)] p-4 rounded-full mb-4">
            <FolderHeart className="h-12 w-12 text-[var(--color-text-tertiary)]" />
          </div>
          <h3 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">No collections found</h3>
          <p className="text-[var(--color-text-secondary)] max-w-md mb-6">
            Create a collection to start saving and categorizing your code reviews.
          </p>
          <Button onClick={handleCreateCollection}>Create your first collection</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {collections.map((collection) => (
            <Card 
              key={collection.id} 
              className="p-6 cursor-pointer hover:shadow-md transition-all hover:-translate-y-1 group relative"
              onClick={() => {
                if (editingCollectionId !== collection.id) {
                  handleSelectCollection(collection);
                }
              }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-xl ${collection.color} bg-opacity-10 text-white`}>
                  <FolderHeart className={`h-6 w-6 ${collection.color.replace('bg-', 'text-')}`} />
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={(e) => handleRenameCollection(e, collection.id, collection.name)}>
                    <Edit2 size={14} className="text-gray-500" />
                  </Button>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={(e) => handleDeleteCollection(e, collection.id)}>
                    <Trash2 size={14} className="text-red-500" />
                  </Button>
                </div>
              </div>
              
              {editingCollectionId === collection.id ? (
                <div className="flex items-center gap-2 mb-1" onClick={e => e.stopPropagation()}>
                  <input 
                    type="text" 
                    value={newCollectionName} 
                    onChange={e => setNewCollectionName(e.target.value)}
                    className="w-full bg-white dark:bg-gray-800 border px-2 py-1 rounded text-sm"
                    autoFocus
                  />
                  <Button size="sm" onClick={(e) => handleSaveRename(e, collection.id)}>Save</Button>
                </div>
              ) : (
                <h3 className="font-semibold text-lg text-[var(--color-text-primary)] mb-1 group-hover:text-[var(--color-primary-500)] transition-colors">
                  {collection.name}
                </h3>
              )}
              
              <p className="text-sm text-[var(--color-text-secondary)]">
                {collection.count} reviews saved
              </p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
