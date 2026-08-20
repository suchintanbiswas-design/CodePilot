export interface User {
  id: string;
  fullName: string;
  username: string;
  email: string;
  avatarUrl?: string;
  role: 'user' | 'admin';
  createdAt: string;
}

export interface UserUpdate {
  fullName?: string;
  username?: string;
  avatarUrl?: string;
}

export interface PasswordChange {
  currentPassword?: string;
  newPassword?: string;
}
