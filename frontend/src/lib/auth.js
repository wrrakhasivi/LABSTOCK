import React, { createContext, useContext, useEffect, useState } from 'react';
import { api, AUTH_STORAGE_KEY } from './api';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(AUTH_STORAGE_KEY);
      if (raw) setUser(JSON.parse(raw));
    } catch (e) { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener('ls-auth-expired', onExpired);
    return () => window.removeEventListener('ls-auth-expired', onExpired);
  }, []);

  const login = async (username, password) => {
    const res = await api.login(username, password);
    const data = { username: res.username, role: res.role, token: res.access_token };
    sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(data));
    setUser(data);
    return data;
  };

  const logout = () => {
    sessionStorage.removeItem(AUTH_STORAGE_KEY);
    setUser(null);
  };

  const isKoordinator = user?.role === 'koordinator';

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isKoordinator }}>
      {children}
    </AuthContext.Provider>
  );
};
