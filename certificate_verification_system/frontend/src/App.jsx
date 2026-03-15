import { BrowserRouter as Router, Routes, Route, Navigate, NavLink } from 'react-router-dom';
import Home from './components/Home';
import Login from './components/Login';
import CollegeDashboard from './components/CollegeDashboard';
import CompanyDashboard from './components/CompanyDashboard';
import StudentView from './components/StudentView';
import Register from './components/Register';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-indigo-100 flex flex-col">
        {/* Top Navigation Bar */}
        <nav className="relative z-50 border-b border-slate-200 bg-white/90 backdrop-blur-md sticky top-0 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <NavLink to="/" className="flex items-center gap-2 group">
                <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center shadow-md group-hover:bg-indigo-600 transition-colors">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <span className="text-xl font-bold tracking-tight text-slate-900">
                  ChainForge Certs
                </span>
              </NavLink>
              <div className="flex items-center space-x-1">
                <NavLink to="/" end className={({ isActive }) => `px-3.5 py-2 rounded-lg text-sm font-bold transition-all ${isActive ? 'text-indigo-600 bg-indigo-50' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'}`}>
                  Home
                </NavLink>
                <NavLink to="/verify" className={({ isActive }) => `px-3.5 py-2 rounded-lg text-sm font-bold transition-all ${isActive ? 'text-indigo-600 bg-indigo-50' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'}`}>
                  Verify
                </NavLink>
                <NavLink to="/login" className={({ isActive }) => `px-3.5 py-2 rounded-lg text-sm font-bold transition-all ${isActive ? 'text-indigo-600 bg-indigo-50' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'}`}>
                  Login
                </NavLink>
                <NavLink to="/register" className={({ isActive }) => `ml-3 px-5 py-2 rounded-full text-sm font-black transition-all shadow-md ${isActive ? 'bg-indigo-600 text-white' : 'bg-slate-900 text-white hover:bg-indigo-600'}`}>
                  Sign Up
                </NavLink>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 flex-1 w-full">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/college" element={<CollegeDashboard />} />
            <Route path="/verify" element={<CompanyDashboard />} />
            <Route path="/student/:certId" element={<StudentView />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>

        {/* Footer */}
        <footer className="relative z-10 border-t border-slate-200 bg-white py-12 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2.5">
              <div className="w-6 h-6 rounded-md bg-slate-900 flex items-center justify-center">
                 <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
              </div>
              <p className="text-sm font-black text-slate-950 tracking-tight">ChainForge Certs</p>
            </div>
            <div className="hidden md:block h-4 w-px bg-slate-200" />
            <p className="text-sm text-slate-500 font-bold tracking-tight">
              Decentralized Trust Protocol for Academic Credentials.
            </p>
            <p className="text-xs text-slate-400 font-bold uppercase tracking-widest">
              © {new Date().getFullYear()} CF Network · Audit Ready
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
