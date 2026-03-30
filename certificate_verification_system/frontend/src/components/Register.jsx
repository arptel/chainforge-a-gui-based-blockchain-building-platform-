import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { KeyRound, Lock, User, Cpu, HardDrive, Eye, EyeOff, ShieldCheck, FolderOpen, RefreshCw } from 'lucide-react';
import { register, browseFolder, getSyncStatus } from '../api';

const LOADING_STEPS = [
    "Setting up account...",
    "Creating database...",
    "Configuring server...",
    "Generating keys...",
    "Finalizing..."
];

export default function Register() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [dbPath, setDbPath] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [loadingStep, setLoadingStep] = useState(0);
    const [syncing, setSyncing] = useState(false);
    const [syncProgress, setSyncProgress] = useState({ local_blocks: 0, network_blocks: 0 });
    const navigate = useNavigate();

    useEffect(() => {
        let interval;
        if (loading) {
            interval = setInterval(() => {
                setLoadingStep((prev) => (prev + 1) % LOADING_STEPS.length);
            }, 1000);
        } else {
            setLoadingStep(0);
        }
        return () => clearInterval(interval);
    }, [loading]);

    const handleBrowse = async () => {
        try {
            const data = await browseFolder();
            if (data.path) {
                setDbPath(data.path);
            }
        } catch (err) {
            console.error('Failed to open directory picker:', err);
            setError('Could not open directory picker. Please type path manually.');
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        if (!username || !password || !dbPath) {
            setError('Please fill in all fields.');
            return;
        }
        
        setError('');
        setLoading(true);

        try {
            const data = await register(username, password, dbPath);
            localStorage.setItem('token', data.access_token);
            
            // Start sync gate — poll until node is synced
            setSyncing(true);
            setLoading(false);
            
            const pollSync = async () => {
                let attempts = 0;
                const maxAttempts = 30; // 60 seconds max
                while (attempts < maxAttempts) {
                    try {
                        const status = await getSyncStatus();
                        setSyncProgress({ 
                            local_blocks: status.local_blocks || 0, 
                            network_blocks: status.network_blocks || 0 
                        });
                        if (status.synced && status.node_online) {
                            setSyncing(false);
                            navigate('/college');
                            return;
                        }
                    } catch (e) {
                        // Node may not be ready yet, keep polling
                    }
                    attempts++;
                    await new Promise(r => setTimeout(r, 2000));
                }
                // Timeout — navigate anyway
                setSyncing(false);
                navigate('/college');
            };
            pollSync();
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed.');
        } finally {
            setLoading(false);
        }
    };

    if (syncing) {
        return (
            <div className="min-h-[70vh] flex items-center justify-center p-4">
                <div className="w-full max-w-md animate-fade-in-up">
                    <div className="soft-card p-12 shadow-2xl text-center">
                        <div className="relative w-20 h-20 mx-auto mb-8">
                            <div className="absolute inset-0 border-4 border-slate-100 rounded-full"></div>
                            <div className="absolute inset-0 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <RefreshCw className="w-8 h-8 text-indigo-600 animate-pulse" />
                            </div>
                        </div>
                        <h2 className="text-2xl font-black text-slate-950 mb-3 tracking-tight">Syncing Blockchain</h2>
                        <p className="text-slate-500 text-sm font-bold mb-8">Your node is synchronizing with the network...</p>
                        
                        {/* Progress bar */}
                        <div className="w-full bg-slate-100 rounded-full h-3 mb-4 overflow-hidden">
                            <div 
                                className="bg-indigo-600 h-3 rounded-full transition-all duration-700 ease-out"
                                style={{ width: syncProgress.network_blocks > 0 
                                    ? `${Math.min(100, (syncProgress.local_blocks / syncProgress.network_blocks) * 100)}%` 
                                    : '15%' 
                                }}
                            />
                        </div>
                        <div className="flex justify-between text-[10px] font-black text-slate-400 uppercase tracking-widest">
                            <span>{syncProgress.local_blocks} blocks</span>
                            <span>{syncProgress.network_blocks > 0 ? `${syncProgress.network_blocks} target` : 'Discovering peers...'}</span>
                        </div>
                        
                        <div className="mt-8 p-4 rounded-xl bg-slate-50 border border-slate-100">
                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest animate-pulse">
                                ● downloading historical blocks from peer nodes
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-[70vh] flex items-center justify-center p-4">
            <div className={`w-full max-w-lg animate-fade-in-up ${error ? 'animate-shake' : ''}`}>
                <div className="soft-card p-12 shadow-2xl relative overflow-hidden">
                    <div className="relative z-10 text-center">
                        <div className="w-16 h-16 rounded-2xl bg-indigo-600 flex items-center justify-center mb-10 mx-auto shadow-xl shadow-indigo-100">
                            <ShieldCheck className="w-8 h-8 text-white" />
                        </div>
                        <h2 className="text-3xl font-black text-slate-950 mb-3 tracking-tighter">Register College</h2>
                        <p className="text-slate-500 mb-12 text-sm font-bold max-w-xs mx-auto leading-relaxed">Create a new college account for certificate verification.</p>

                        {error && (
                            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm mb-10 font-black animate-in fade-in zoom-in-95">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleRegister} className="space-y-10 text-left">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div>
                                    <label className="block text-[11px] font-black text-slate-400 tracking-[0.2em] uppercase mb-3 ml-1">Username</label>
                                    <div className="relative group">
                                        <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-600 transition-colors" />
                                        <input
                                            type="text"
                                            value={username}
                                            onChange={(e) => setUsername(e.target.value)}
                                            className="slate-input w-full rounded-xl py-4.5 pl-12 pr-4 text-sm font-bold tracking-tight placeholder:text-slate-300"
                                            placeholder="college_a"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-[11px] font-black text-slate-400 tracking-[0.2em] uppercase mb-3 ml-1">Password</label>
                                    <div className="relative group">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-600 transition-colors" />
                                        <input
                                            type={showPassword ? "text" : "password"}
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            className="slate-input w-full rounded-xl py-4.5 pl-12 pr-12 text-sm font-bold tracking-tight placeholder:text-slate-300"
                                            placeholder="••••••••"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-900 transition-colors"
                                        >
                                            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <label className="block text-[11px] font-black text-slate-400 tracking-[0.2em] uppercase mb-3 ml-1">Data Storage Path</label>
                                <div className="flex gap-4">
                                    <div className="relative group flex-1">
                                        <HardDrive className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-600 transition-colors" />
                                        <input
                                            type="text"
                                            value={dbPath}
                                            onChange={(e) => setDbPath(e.target.value)}
                                            className="slate-input w-full rounded-xl py-4.5 pl-12 pr-4 text-sm font-bold tracking-tight placeholder:text-slate-300"
                                            placeholder={`e.g., C:/Users/Docs/chain.db`}
                                        />
                                    </div>
                                    <button
                                        type="button"
                                        onClick={handleBrowse}
                                        className="px-6 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 font-black transition-all flex items-center justify-center gap-2 group whitespace-nowrap"
                                    >
                                        <FolderOpen className="w-4 h-4 group-hover:scale-110 transition-transform" />
                                        <span className="text-[10px] uppercase tracking-widest">Browse</span>
                                    </button>
                                </div>
                                <p className="text-[10px] text-slate-400 mt-4 ml-1 font-black uppercase tracking-widest leading-relaxed">
                                   Required: Where your college data will be stored.
                                </p>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full mt-6 btn-primary text-white font-black py-5.5 rounded-xl shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex flex-col items-center justify-center gap-1 active:scale-[0.98]"
                            >
                                {loading ? (
                                    <>
                                        <div className="flex items-center gap-3">
                                            <div className="w-4 h-4 border-3 border-white/20 border-t-white rounded-full animate-spin" />
                                            <span className="text-sm font-black uppercase tracking-widest">Registering...</span>
                                        </div>
                                        <span className="text-[10px] uppercase tracking-[0.25em] opacity-60 font-black mt-1.5 animate-pulse-soft">
                                            {LOADING_STEPS[loadingStep]}
                                        </span>
                                    </>
                                ) : (
                                    <span className="tracking-widest uppercase text-xs">Register</span>
                                )}
                            </button>
                        </form>
                        
                        <div className="mt-12 pt-10 border-t border-slate-100 text-center">
                            <button
                                type="button"
                                onClick={() => navigate('/login')}
                                className="text-slate-400 hover:text-slate-900 font-black transition-colors text-[10px] uppercase tracking-[0.2em] flex items-center justify-center gap-3 mx-auto group"
                            >
                                <svg className="w-4 h-4 group-hover:-translate-x-1.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
                                </svg>
                                Back to Login
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
