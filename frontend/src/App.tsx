import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import GraphDiscovery from './pages/GraphDiscovery';
import Chat from './pages/Chat';
import LitReview from './pages/LitReview';
import Gaps from './pages/Gaps';
import Profile from './pages/Profile';

export const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* Public auth routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Private app pages (Module 1 login wall dependencies) */}
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/graph" element={<GraphDiscovery />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/review" element={<LitReview />} />
          <Route path="/gaps" element={<Gaps />} />
          <Route path="/profile" element={<Profile />} />
          
          {/* Redirect to dashboard as fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </Router>
  );
};
export default App;
