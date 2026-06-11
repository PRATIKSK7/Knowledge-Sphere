import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { 
  BookOpen, 
  LayoutDashboard, 
  Network, 
  UploadCloud, 
  MessageSquare, 
  Lightbulb, 
  FileText, 
  User as UserIcon, 
  LogOut,
  Menu,
  X
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', name: 'Dashboard', icon: LayoutDashboard },
    { path: '/documents', name: 'Documents', icon: UploadCloud },
    { path: '/graph', name: 'Knowledge Graph', icon: Network },
    { path: '/chat', name: 'Research Chat', icon: MessageSquare },
    { path: '/review', name: 'Literature Review', icon: FileText },
    { path: '/gaps', name: 'Research Gaps', icon: Lightbulb },
  ];

  return (
    <nav className="glass-panel border-b border-slate-800 sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
      {/* Brand logo */}
      <Link to="/dashboard" className="flex items-center gap-3 group">
        <div className="bg-gradient-to-r from-blue-500 to-indigo-600 p-2.5 rounded-xl shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-all">
          <BookOpen className="h-6 w-6 text-white" />
        </div>
        <div>
          <span className="font-bold text-lg tracking-wide bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            KNOWLEDGE SPHERE
          </span>
          <span className="block text-[10px] text-blue-400 tracking-widest uppercase font-semibold">
            Research Intelligence
          </span>
        </div>
      </Link>

      {/* Nav Menu */}
      <div className="hidden lg:flex items-center gap-1.5">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-blue-500/10 border border-blue-500/30 text-blue-400 shadow-inner'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.name}
            </Link>
          );
        })}
      </div>

      {/* User Session Actions */}
      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-3">
            <Link to="/profile" className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 hover:bg-slate-850 transition-all">
              <div className="bg-slate-800 h-8 w-8 rounded-full flex items-center justify-center text-blue-400 border border-blue-500/20 font-bold uppercase">
                {user.full_name?.charAt(0) || 'U'}
              </div>
              <div className="hidden sm:block text-left">
                <span className="block text-xs font-semibold text-slate-200 leading-tight">
                  {user.full_name}
                </span>
                <span className="block text-[10px] text-slate-500 font-medium capitalize leading-none">
                  {user.role}
                </span>
              </div>
            </Link>

            <button
              onClick={handleLogout}
              className="p-2 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all duration-200 border border-transparent hover:border-rose-500/20"
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/40 transition-all"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        )}
      </div>

      {/* Mobile Nav Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="absolute top-[100%] left-0 w-full glass-panel border-b border-slate-800 lg:hidden py-4 px-6 flex flex-col gap-2 shadow-2xl">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-blue-500/10 border border-blue-500/30 text-blue-400 shadow-inner'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
                }`}
              >
                <Icon className="h-5 w-5" />
                {item.name}
              </Link>
            );
          })}
        </div>
      )}
    </nav>
  );
};
export default Navbar;
