import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Home from './components/Home';
import Login from './components/Login';
import CollegeDashboard from './components/CollegeDashboard';
import CompanyDashboard from './components/CompanyDashboard';
import StudentView from './components/StudentView';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-neutral-950 text-neutral-100 font-sans selection:bg-indigo-500/30">
        {/* Background Ambient Glow */}
        <div className="fixed inset-0 z-0 flex items-center justify-center overflow-hidden pointer-events-none">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600/20 blur-[120px] rounded-full mix-blend-screen" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/20 blur-[120px] rounded-full mix-blend-screen" />
        </div>

        {/* Top Navigation Bar */}
        <nav className="relative z-10 border-b border-white/10 bg-black/40 backdrop-blur-md sticky top-0">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-neutral-400">
                  ChainForge Certs
                </span>
              </div>
              <div className="flex space-x-4">
                <a href="/" className="text-sm font-medium text-neutral-400 hover:text-white transition-colors">Home</a>
                <a href="/verify" className="text-sm font-medium text-neutral-400 hover:text-white transition-colors">Verify</a>
                <a href="/login" className="text-sm font-medium text-neutral-400 hover:text-white transition-colors">College Portal</a>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/college" element={<CollegeDashboard />} />
            <Route path="/verify" element={<CompanyDashboard />} />
            <Route path="/student/:certId" element={<StudentView />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
