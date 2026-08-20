import api from '@/config/api';
import { Review, ReviewCreatePayload, ReviewFilter, LanguageDetectionResult } from '@/types/review';

export const reviewService = {
  create: async (data: ReviewCreatePayload): Promise<Review> => {
    const formData = new FormData();
    formData.append('req_data', JSON.stringify(data));
    const response = await api.post<Review>('/reviews', formData);
    return response.data;
  },

  upload: async (formData: FormData): Promise<Review> => {
    const response = await api.post<Review>('/reviews', formData);
    return response.data;
  },

  getById: async (id: string): Promise<Review> => {
    const response = await api.get<Review>(`/reviews/${id}`);
    return response.data;
  },

  list: async (filters?: ReviewFilter): Promise<{items: Review[], total: number, page: number, size: number}> => {
    const response = await api.get<{items: Review[], total: number, page: number, size: number}>('/reviews', { params: filters });
    return response.data;
  },

  detectLanguage: async (sourceCode: string, language: string, fileName?: string): Promise<LanguageDetectionResult> => {
    const formData = new FormData();
    formData.append('req_data', JSON.stringify({ source_code: sourceCode, language, file_name: fileName }));
    const response = await api.post<{success: boolean, data: LanguageDetectionResult}>('/reviews/detect-language', formData);
    return response.data.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/reviews/${id}`);
  },

  favorite: async (id: string): Promise<void> => {
    await api.post(`/favorites/reviews/${id}`);
  },

  duplicate: async (id: string): Promise<Review> => {
    const response = await api.post<Review>(`/reviews/${id}/duplicate`);
    return response.data;
  },

  downloadReport: async (id: string): Promise<Blob> => {
    const response = await api.get(`/reviews/${id}/report?type=pdf`, { responseType: 'blob' });
    return response.data;
  },
};
