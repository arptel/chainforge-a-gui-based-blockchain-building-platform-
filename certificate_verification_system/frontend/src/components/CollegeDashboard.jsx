import { useState, useEffect } from 'react';
import { issueCertificate, revokeCertificate, getHistory } from '../api';
import { FileSignature, ShieldAlert, LogOut, CheckCircle2, Copy, ExternalLink, GraduationCap, Clock, Award, ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function CollegeDashboard() {
    const navigate = useNavigate();
    const [collegeName, setCollegeName] = useState('College Dashboard');
    const [formData, setFormData] = useState({ studentName: '', degree: 'B.S. Computer Science', year: new Date().getFullYear() });
    const [revokeId, setRevokeId] = useState('');

    const [issueStatus, setIssueStatus] = useState(null);
    const [revokeStatus, setRevokeStatus] = useState(null);
    const [loading, setLoading] = useState(false);
    const [copyId, setCopyId] = useState(null);

    const [recentCerts, setRecentCerts] = useState([]);
    const [balance, setBalance] = useState(0);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                if (payload.sub) {
                    const formatted = payload.sub.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                    setCollegeName(formatted);
                }
            } catch (e) {
                console.error("Token decoding failed", e);
            }
        }
        fetchHistory();
    }, []);

    const fetchHistory = async () => {
        try {
            const history = await getHistory();
            setRecentCerts(history);
            
            // Fetch balance alongside history
            const { getBalance } = await import('../api');
            const balRes = await getBalance();
            setBalance(balRes.balance || 0);
        } catch (err) {
            console.error("Failed to fetch history/balance:", err);
        }
    };

    const handleIssue = async (e) => {
        e.preventDefault();
        setLoading(true);
        setIssueStatus(null);
        try {
            const res = await issueCertificate(formData.studentName, formData.degree, formData.year);
            setIssueStatus({ type: 'success', msg: `Certificate Issued! ID: ${res.cert_id}` });
            
            // Refresh full history from on-chain state
            await fetchHistory();
            setFormData({ studentName: '', degree: 'B.S. Computer Science', year: new Date().getFullYear() });
        } catch (err) {
            setIssueStatus({ type: 'error', msg: err?.response?.data?.detail || 'Issuance failed.' });
        } finally {
            setLoading(false);
        }
    };

    const handleRevoke = async (e) => {
        e.preventDefault();
        setLoading(true);
        setRevokeStatus(null);
        try {
            const res = await revokeCertificate(revokeId);
            setRevokeStatus({ type: 'success', msg: 'Certificate Revoked successfully.' });
            setRevokeId('');
        } catch (err) {
            setRevokeStatus({ type: 'error', msg: err?.response?.data?.detail || 'Revocation failed.' });
        } finally {
            setLoading(false);
        }
    };

    const copyToClipboard = (id) => {
        navigator.clipboard.writeText(id);
        setCopyId(id);
        setTimeout(() => setCopyId(null), 2000);
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/');
    };

    return (
        <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-1000 relative">
            {/* Subtle background pattern */}
            <div className="absolute inset-0 bg-blockchain-pattern pointer-events-none opacity-20 -z-10 rounded-[3rem]"></div>
            {/* Header Section */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-10 border-b border-slate-200 pb-12">
                <div>
                    <div className="flex items-center gap-3 mb-4">
                        <span className="px-3 py-1 rounded bg-slate-900 text-[10px] font-black text-white uppercase tracking-[0.2em]">Management</span>
                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-100">
                             <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                             <span className="text-[10px] font-black text-emerald-700 uppercase tracking-widest">Online</span>
                        </div>
                    </div>
                    <h1 className="text-4xl font-black text-slate-950 tracking-tight leading-tight">
                        {collegeName}
                    </h1>
                    <p className="text-slate-500 mt-2.5 font-bold tracking-tight">Manage and issue certificates securely.</p>
                </div>
                <button 
                    onClick={handleLogout} 
                    className="group flex items-center gap-3 px-8 py-3.5 rounded-xl bg-white border-2 border-slate-200 hover:border-red-600 transition-all text-sm font-black text-slate-950 hover:text-red-600 shadow-sm active:scale-95"
                >
                    <LogOut className="w-4 h-4 text-slate-400 group-hover:text-red-600" /> 
                    Logout
                </button>
            </div>

            {/* Quick Stats Strip */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-2xl">
                {/* Balance Card */}
                <div className="p-6 rounded-2xl bg-white border-2 border-slate-200 flex items-center gap-5 shadow-sm">
                    <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center">
                        <span className="text-xl">🪙</span>
                    </div>
                    <div>
                        <p className="text-[10px] text-slate-400 font-black uppercase tracking-[0.2em] mb-1">Current Balance</p>
                        <div className="flex items-baseline gap-2">
                           <span className="text-2xl font-black text-emerald-600 tracking-tight">{balance.toFixed(1)}</span>
                           <span className="text-sm font-bold text-slate-400">CF</span>
                        </div>
                    </div>
                </div>

                {/* Total Issued Card */}
                <div className="p-6 rounded-2xl bg-white border-2 border-slate-200 flex items-center gap-5 shadow-sm">
                    <div className="w-12 h-12 rounded-xl bg-indigo-100 flex items-center justify-center">
                        <FileSignature className="w-5 h-5 text-indigo-600" />
                    </div>
                    <div>
                        <p className="text-[10px] text-slate-400 font-black uppercase tracking-[0.2em] mb-1">Total Issued</p>
                        <div className="flex items-baseline gap-2">
                           <span className="text-2xl font-black text-indigo-600 tracking-tight">{recentCerts.length}</span>
                           <span className="text-sm font-bold text-slate-400">Certs</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                {/* Issue Certificate Zone */}
                <div className="p-10 soft-card relative overflow-hidden group border-indigo-100">
                    <div className="flex items-center gap-6 mb-12">
                        <div className="w-14 h-14 rounded-2xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-100">
                            <FileSignature className="w-7 h-7 text-white" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-slate-950 tracking-tight">Issue Certificate</h2>
                            <p className="text-[10px] text-slate-400 font-black uppercase tracking-[0.15em] mt-1">Create a new student record</p>
                        </div>
                    </div>

                    <form onSubmit={handleIssue} className="relative z-10 space-y-8">
                        <div>
                            <label className="block text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3 ml-1">Student Name</label>
                            <input
                                required type="text" value={formData.studentName} 
                                onChange={(e) => setFormData({ ...formData, studentName: e.target.value })}
                                className="slate-input w-full rounded-xl py-4.5 px-5 font-black text-slate-950 tracking-tight"
                                placeholder="e.g., John Doe"
                            />
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                            <div>
                                <label className="block text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3 ml-1">Degree / Course</label>
                                <input
                                    required type="text" value={formData.degree} 
                                    onChange={(e) => setFormData({ ...formData, degree: e.target.value })}
                                    className="slate-input w-full rounded-xl py-4.5 px-5 font-bold text-slate-950 text-sm tracking-tight"
                                />
                            </div>
                            <div>
                                <label className="block text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3 ml-1">Year</label>
                                <input
                                    required type="number" value={formData.year} 
                                    onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                                    className="slate-input w-full rounded-xl py-4.5 px-5 font-black text-slate-950 font-mono tracking-widest text-lg"
                                />
                            </div>
                        </div>

                        {issueStatus && (
                            <div className={`p-5 rounded-xl text-sm border flex items-center gap-4 animate-in fade-in zoom-in-95 font-black tracking-tight ${issueStatus.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                                {issueStatus.type === 'success' ? <CheckCircle2 className="w-5 h-5 flex-shrink-0" /> : <ShieldAlert className="w-5 h-5 flex-shrink-0" />}
                                <span>{issueStatus.msg}</span>
                            </div>
                        )}

                        <button 
                            disabled={loading || !formData.studentName} 
                            type="submit" 
                            className="w-full mt-4 btn-primary font-black py-5 rounded-xl transition-all shadow-xl active:scale-[0.98] disabled:opacity-40 uppercase tracking-widest text-xs"
                        >
                            {loading ? 'Issuing...' : 'Issue Certificate'}
                        </button>
                    </form>
                </div>

                {/* Revoke Certificate Zone */}
                <div className="p-10 soft-card relative overflow-hidden group border-slate-200">
                    <div className="flex items-center gap-6 mb-12">
                        <div className="w-14 h-14 rounded-2xl bg-white border-2 border-red-100 flex items-center justify-center shadow-sm">
                            <ShieldAlert className="w-7 h-7 text-red-600" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-slate-950 tracking-tight">Revoke Certificate</h2>
                            <p className="text-[10px] text-slate-400 font-black uppercase tracking-[0.15em] mt-1">Cancel an existing record</p>
                        </div>
                    </div>

                    <p className="text-sm text-slate-500 mb-10 leading-relaxed font-bold tracking-tight">
                       Enter the Certificate ID to permanently cancel a record.
                    </p>

                    <form onSubmit={handleRevoke} className="relative z-10 space-y-8">
                        <div>
                            <label className="block text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3 ml-1">Certificate ID</label>
                            <input
                                required type="text" placeholder="CERT-XXXX-XXXX" value={revokeId} 
                                onChange={(e) => setRevokeId(e.target.value)}
                                className="slate-input w-full rounded-xl py-5 px-5 font-mono text-sm placeholder:text-slate-300 font-black tracking-widest uppercase"
                            />
                        </div>

                        {revokeStatus && (
                            <div className={`p-5 rounded-xl text-sm border flex items-center gap-4 animate-in fade-in zoom-in-95 font-bold ${revokeStatus.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                                {revokeStatus.type === 'success' ? <CheckCircle2 className="w-5 h-5 flex-shrink-0" /> : <ShieldAlert className="w-5 h-5 flex-shrink-0" />}
                                <span>{revokeStatus.msg}</span>
                            </div>
                        )}

                        <button 
                            disabled={loading || !revokeId} 
                            type="submit" 
                            className="w-full mt-4 bg-white border-2 border-slate-900 text-slate-950 hover:bg-red-600 hover:text-white hover:border-red-600 font-black py-5 rounded-xl transition-all active:scale-[0.98] disabled:opacity-40 uppercase tracking-widest text-xs shadow-sm"
                        >
                            {loading ? 'Revoking...' : 'Revoke Certificate'}
                        </button>
                    </form>
                </div>
            </div>

            {/* Session Activity Ledger */}
            <div className="mt-16 p-12 soft-card bg-slate-100/30 border-dashed border-slate-200 min-h-[400px]">
                <div className="flex items-center justify-between mb-12">
                    <div>
                        <h3 className="text-2xl font-black text-slate-950 flex items-center gap-4">
                            <Clock className="w-8 h-8 text-slate-300" /> Recent Activity
                        </h3>
                        <p className="text-xs text-slate-400 font-bold mt-2 uppercase tracking-widest">History of certificates issued</p>
                    </div>
                    <div className="flex items-center gap-3 bg-white px-5 py-2.5 rounded-xl border border-slate-200 shadow-sm">
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Total:</span>
                        <span className="text-sm font-black text-slate-950">{recentCerts.length}</span>
                    </div>
                </div>

                {recentCerts.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {recentCerts.map((c, i) => (
                            <div key={i} className="group flex justify-between items-center p-8 rounded-2xl bg-white border border-slate-200 hover:border-indigo-600/40 hover:shadow-2xl hover:shadow-indigo-900/5 transition-all animate-in slide-in-from-bottom-3 fade-in" style={{ animationDelay: `${i * 120}s` }}>
                                <div className="space-y-3">
                                    <div className="flex items-center gap-4">
                                        <p className="font-black text-slate-950 tracking-tight text-xl">{c.studentName}</p>
                                        <div className="px-2 py-0.5 rounded bg-slate-50 text-[10px] font-black text-slate-400 uppercase tracking-tighter">{c.timestamp}</div>
                                        {c.isRevoked && (
                                            <div className="px-2 py-0.5 rounded bg-red-50 text-[10px] font-black text-red-600 uppercase tracking-tighter border border-red-100">Revoked</div>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-2.5 text-sm text-slate-500 font-bold">
                                        <GraduationCap className="w-4 h-4 text-slate-300" />
                                        <span>{c.degree} · {c.year}</span>
                                    </div>
                                    <div className="flex items-center gap-4 pt-4 border-t border-slate-50">
                                        <p className="text-[10px] text-indigo-600 font-black tracking-[0.15em] uppercase">ID: {c.certId ? c.certId.slice(0, 12) : 'N/A'}...</p>
                                        <button 
                                            onClick={() => c.certId && copyToClipboard(c.certId)} 
                                            className="text-slate-300 hover:text-indigo-600 transition-colors bg-slate-50 p-1.5 rounded-md"
                                            title="Copy ID"
                                        >
                                            {copyId === c.certId ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                                        </button>
                                    </div>
                                </div>
                                <button 
                                    onClick={() => navigate(`/student/${c.certId}`)} 
                                    className="w-14 h-14 rounded-2xl bg-slate-50 border border-slate-200 text-slate-400 hover:bg-slate-950 hover:text-white transition-all shadow-sm group-hover:scale-110 flex items-center justify-center group/btn"
                                    title="View Certificate"
                                >
                                    <ExternalLink className="w-6 h-6 group-hover/btn:scale-110 transition-transform" />
                                </button>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center py-28 text-center bg-white/40 rounded-[2.5rem] border-2 border-dashed border-slate-200 mt-4">
                        <div className="w-24 h-24 rounded-[2rem] bg-slate-100 flex items-center justify-center border border-slate-200 mb-8 shadow-inner">
                            <Award className="w-12 h-12 text-slate-300 animate-float" />
                        </div>
                        <p className="text-slate-400 font-black text-sm uppercase tracking-[0.2em]">No Recent Activity</p>
                        <p className="text-slate-300 text-xs mt-3 font-bold max-w-[320px] leading-relaxed">Issued certificates will appear here.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
