export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  NEW_REVIEW: '/reviews/new',
  REVIEW_DETAIL: (id: string | number) => `/reviews/${id}`,
  HISTORY: '/history',
  ANALYTICS: '/analytics',
  FAVORITES: '/favorites',
  PROFILE: '/profile',
  SETTINGS: '/settings',
  ADMIN: '/admin',
};

