import api from '@/config/api';
import { ReviewSummary } from '@/types/review';

export interface Collection {
  id: string;
  name: string;
  count: number;
  color: string;
}

export const favoriteService = {
  getCollections: async (): Promise<Collection[]> => {
    const response = await api.get<{success: boolean, data: Collection[]}>('/favorites/collections');
    return response.data.data;
  },

  getCollectionReviews: async (collectionId: string): Promise<ReviewSummary[]> => {
    const response = await api.get<{success: boolean, data: ReviewSummary[]}>(`/favorites/collections/${collectionId}/reviews`);
    return response.data.data;
  },

  createCollection: async (name: string, color?: string): Promise<Collection> => {
    const response = await api.post<{success: boolean, data: Collection}>('/favorites/collections', { name, color });
    return response.data.data;
  },

  updateCollection: async (collectionId: string, name: string): Promise<Collection> => {
    const response = await api.put<{success: boolean, data: Collection}>(`/favorites/collections/${collectionId}`, { name });
    return response.data.data;
  },

  deleteCollection: async (collectionId: string): Promise<void> => {
    await api.delete(`/favorites/collections/${collectionId}`);
  },

  moveReview: async (reviewId: string, _fromCollectionId: string, toCollectionId: string): Promise<void> => {
    await api.put(`/favorites/reviews/${reviewId}/move?collection_id=${toCollectionId}`);
  },
  
  removeReview: async (reviewId: string, collectionId: string): Promise<void> => {
    await api.delete(`/favorites/collections/${collectionId}/reviews/${reviewId}`);
  }
};
