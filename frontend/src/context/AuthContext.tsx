"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import api from '@/lib/api';

interface User {
  id: number;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => {},
  logout: () => {},
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        if (pathname !== '/login') router.push('/login');
        return;
      }

      try {
        const response = await api.get('/me');
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem('token');
        setUser(null);
        if (pathname !== '/login') router.push('/login');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [pathname, router]);

  const login = async (token: string) => {
    localStorage.setItem('token', token);
    try {
      const response = await api.get('/me');
      setUser(response.data);
      window.location.href = '/dashboard';
    } catch (err) {
      console.error("Login verification failed", err);
      // Optional: Clear token if you want strict failure
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
