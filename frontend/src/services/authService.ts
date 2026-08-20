import api from '@/config/api';
import { LoginRequest, RegisterRequest, TokenResponse } from '@/types/auth';
import { User } from '@/types/user';

export const authService = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<{success: boolean, data: TokenResponse}>('/auth/login', data);
    return response.data.data;
  },

  register: async (data: RegisterRequest): Promise<TokenResponse> => {
    // The backend registers and might not return token directly based on prompt, but wait:
    // AuthContext expects register to return TokenResponse. 
    // We will call register, then login to get the token.
    await api.post<{success: boolean, data: User}>('/auth/register', {
      email: data.email,
      username: data.username,
      password: data.password,
      full_name: data.fullName
    });
    const loginResponse = await api.post<{success: boolean, data: TokenResponse}>('/auth/login', {
      email: data.email,
      password: data.password
    });
    return loginResponse.data.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<{success: boolean, data: User}>('/auth/me');
    return response.data.data;
  },

  logout: async () => {
    try {
      await api.post<{success: boolean, data: null}>('/auth/logout');
    } catch (error) {
      // Ignore logout errors
    }
    localStorage.removeItem('token');
  },
  
  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await api.post<{success: boolean, data: TokenResponse}>('/auth/refresh', { refresh_token: refreshToken });
    return response.data.data;
  }
};
