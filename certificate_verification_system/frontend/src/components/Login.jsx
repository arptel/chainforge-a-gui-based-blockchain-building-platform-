import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, getSyncStatus } from '../api';
import { KeyRound, Lock, User, Eye, EyeOff, ShieldCheck, RefreshCw } from 'lucide-react';

export default function Login() {
    const [username, setUsername] = useState('college_a');
    const [password, setPassword] = useState('password123');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [syncing, setSyncing] = useState(false);
    const [syncProgress, setSyncProgress] = useState({ local_blocks: 0, network_blocks: 0 });
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const data = await login(username, password);
            localStorage.setItem('token', data.access_token);
            
            // Start sync gate — poll until node is synced
            setSyncing(true);
            setLoading(false);
            
            const pollSync = async () => {
                let attempts = 0;
                const maxAttempts = 20; // 40 seconds max
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
            setError('The credentials provided are incorrect.');
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
                            <div className="absolute inset-0 border-4 border-slate-900 border-t-transparent rounded-full animate-spin"></div>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <RefreshCw className="w-8 h-8 text-slate-900 animate-pulse" />
                            </div>
                        </div>
                        <h2 className="text-2xl font-black text-slate-950 mb-3 tracking-tight">Syncing Node</h2>
                        <p className="text-slate-500 text-sm font-bold mb-8">Ensuring your blockchain node is up to date...</p>
                        
                        <div className="w-full bg-slate-100 rounded-full h-3 mb-4 overflow-hidden">
                            <div 
                                className="bg-slate-900 h-3 rounded-full transition-all duration-700 ease-out"
                                style={{ width: syncProgress.network_blocks > 0 
                                    ? `${Math.min(100, (syncProgress.local_blocks / syncProgress.network_blocks) * 100)}%` 
                                    : '30%' 
                                }}
                            />
                        </div>
                        <div className="flex justify-between text-[10px] font-black text-slate-400 uppercase tracking-widest">
                            <span>{syncProgress.local_blocks} blocks synced</span>
                            <span>{syncProgress.network_blocks > 0 ? `${syncProgress.network_blocks} total` : 'Connecting...'}</span>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-[70vh] flex items-center justify-center p-4">
            <div className={`w-full max-w-md animate-fade-in-up ${error ? 'animate-shake' : ''}`}>
                <div className="soft-card p-10 shadow-2xl relative overflow-hidden">
                    <div className="relative z-10">
                        <div className="w-16 h-16 rounded-2xl bg-slate-900 flex items-center justify-center mb-8 mx-auto shadow-xl">
                            <ShieldCheck className="w-8 h-8 text-white" />
                        </div>
                        <h2 className="text-3xl font-black text-center text-slate-950 mb-3 tracking-tight">College Login</h2>
                        <p className="text-slate-500 text-center mb-12 text-sm font-bold uppercase tracking-tight">Authorized Access Only</p>

                        {error && (
                            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm mb-10 text-center font-black animate-in fade-in zoom-in-95">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleLogin} className="space-y-8">
                            <div>
                                <label className="block text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3 ml-1">Username</label>
                                <div className="relative group">
                                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-600 transition-colors" />
                                    <input
                                        type="text"
                                        required
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        className="slate-input w-full rounded-xl py-4.5 pl-12 pr-4 font-bold text-sm tracking-tight placeholder:text-slate-300"
                                        placeholder="college_code"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3 ml-1">Password</label>
                                <div className="relative group">
                                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-600 transition-colors" />
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        required
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="slate-input w-full rounded-xl py-4.5 pl-12 pr-12 font-bold text-sm tracking-tight placeholder:text-slate-300"
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

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full mt-6 btn-secondary text-white font-black py-5 rounded-xl shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 active:scale-[0.98]"
                            >
                                {loading ? (
                                    <div className="w-5 h-5 border-3 border-white/20 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <KeyRound className="w-4 h-4" />
                                )}
                                <span className="tracking-widest uppercase text-xs">{loading ? 'Logging in...' : 'Login'}</span>
                            </button>
                        </form>

                        <div className="mt-12 pt-10 border-t border-slate-100 text-center">
                            <p className="text-xs text-slate-400 font-black uppercase tracking-[0.1em] mb-6">New College?</p>
                            <button
                                type="button"
                                onClick={() => navigate('/register')}
                                className="w-full bg-white border-2 border-slate-200 text-slate-900 font-black py-4 rounded-xl hover:border-slate-900 transition-all flex items-center justify-center gap-2 group text-sm shadow-sm"
                            >
                                <span>Sign Up</span>
                                <svg className="w-4 h-4 text-slate-400 group-hover:translate-x-1 group-hover:text-slate-900 transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
