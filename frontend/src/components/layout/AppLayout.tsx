import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import Navbar from './Navbar';

export const AppLayout: React.FC = () => {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0f19]">
      <Navbar />
      <main className="flex-1 w-full max-w-7xl mx-auto px-6 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-slate-900/60 py-6 text-center text-xs text-slate-500 glass-panel">
        <p>© 2026 Knowledge Sphere AI. Built for Academic Research Intelligence. All rights reserved.</p>
      </footer>
    </div>
  );
};
export default AppLayout;
