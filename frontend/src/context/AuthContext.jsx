import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem('token');
      if (savedToken) {
        try {
          const res = await api.get('/auth/me');
          setUser(res.data);
          localStorage.setItem('user', JSON.stringify(res.data));
        } catch (err) {
          console.error('Session verification failed:', err);
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (identifier, password) => {
    // Backend accepts both email and identifier (roll number / employee ID)
    const payload = {
      identifier: identifier.trim(),
      password,
    };
    const res = await api.post('/auth/login', payload);
    const accessToken = res.data.access_token;
    localStorage.setItem('token', accessToken);
    setToken(accessToken);

    // Fetch user profile
    const profileRes = await api.get('/auth/me', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    setUser(profileRes.data);
    localStorage.setItem('user', JSON.stringify(profileRes.data));
    return profileRes.data;
  };

  const register = async ({ fullName, rollNumber, password }) => {
    const payload = {
      full_name: fullName.trim(),
      roll_number: rollNumber.trim(),
      password,
    };
    const res = await api.post('/auth/register', payload);
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
      localStorage.setItem('user', JSON.stringify(res.data));
      return res.data;
    } catch (err) {
      console.error('Failed to refresh user profile:', err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated: !!user && !!token,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
