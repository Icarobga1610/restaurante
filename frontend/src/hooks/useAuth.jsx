import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { auth as authApi } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  // Guards against concurrent refresh calls and logout races.
  const refreshPromise = useRef(null);

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (savedToken && savedUser) {
      setToken(savedToken);
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('refresh');
      }
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    const handleUnauthorized = () => {
      setToken(null);
      setUser(null);
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  // Silently rotate the access token using the server-side refresh token.
  const refresh = async () => {
    if (refreshPromise.current) return refreshPromise.current;
    refreshPromise.current = (async () => {
      const refreshToken = localStorage.getItem('refresh');
      if (!refreshToken) throw new Error('No refresh token');
      const response = await authApi.refresh(refreshToken);
      const { access_token, refresh_token: newRefresh, user: userData } = response.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('refresh', newRefresh);
      localStorage.setItem('user', JSON.stringify(userData));
      setToken(access_token);
      setUser(userData);
      return access_token;
    })();
    try {
      return await refreshPromise.current;
    } finally {
      refreshPromise.current = null;
    }
  };

  const login = async (username, password) => {
    const response = await authApi.login(username, password);
    const { access_token, refresh_token, user: userData } = response.data;
    localStorage.setItem('token', access_token);
    localStorage.setItem('refresh', refresh_token);
    localStorage.setItem('user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh');
    try {
      if (refreshToken) await authApi.logout(refreshToken);
    } catch {
      // Best-effort: even if the server call fails, clear local state.
    }
    localStorage.removeItem('token');
    localStorage.removeItem('refresh');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const hasRole = (...roles) => {
    if (!user) return false;
    return roles.includes(user.role_name);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, refresh, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
