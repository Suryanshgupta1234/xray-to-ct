import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Activity,
  Layers,
  UploadCloud,
  History,
  Info,
  ShieldCheck,
  Sun,
  Moon,
  LogOut,
  User,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

export const Navbar = () => {
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navLinkClass = (path) => {
    const active = location.pathname === path;
    return `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
      active
        ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
        : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
    }`;
  };

  return (
    <nav className="sticky top-0 z-40 bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white group-hover:text-cyan-400 transition-colors">
                  XRAY<span className="text-cyan-400">→</span>CT
                </span>
                <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                  Research
                </span>
              </div>
              <p className="text-[11px] text-slate-400 tracking-wide font-mono -mt-0.5">
                pix2pix Translation
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-1.5">
            {isAuthenticated && (
              <>
                <Link to="/dashboard" className={navLinkClass('/dashboard')}>
                  <Layers className="w-4 h-4" />
                  Dashboard
                </Link>
                <Link to="/upload" className={navLinkClass('/upload')}>
                  <UploadCloud className="w-4 h-4" />
                  Translate
                </Link>
                <Link to="/history" className={navLinkClass('/history')}>
                  <History className="w-4 h-4" />
                  History
                </Link>
              </>
            )}
            <Link to="/model-info" className={navLinkClass('/model-info')}>
              <Info className="w-4 h-4" />
              Model Specs
            </Link>
            {isAdmin && (
              <Link to="/admin" className={navLinkClass('/admin')}>
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Admin
              </Link>
            )}
          </div>

          {/* Right Action Controls */}
          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              aria-label="Toggle theme"
              className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
            >
              {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-blue-400" />}
            </button>

            {isAuthenticated ? (
              <div className="flex items-center gap-2.5 pl-2 border-l border-slate-800">
                <div className="flex items-center gap-2 text-sm text-slate-300">
                  <div className="w-7 h-7 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-400 flex items-center justify-center font-medium text-xs">
                    {user?.full_name ? user.full_name.charAt(0).toUpperCase() : <User className="w-3.5 h-3.5" />}
                  </div>
                  <span className="hidden lg:inline-block max-w-[120px] truncate text-xs text-slate-300 font-medium">
                    {user?.email}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  title="Log out"
                  className="p-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-950/30 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-3.5 py-1.5 rounded-lg text-sm text-slate-300 hover:text-white transition-colors"
                >
                  Log In
                </Link>
                <Link
                  to="/register"
                  className="px-3.5 py-1.5 rounded-lg text-sm font-medium bg-cyan-600 hover:bg-cyan-500 text-white transition-all shadow-md shadow-cyan-600/20"
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
