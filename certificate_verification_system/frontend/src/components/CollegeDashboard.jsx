import { useState } from 'react';
import { issueCertificate, revokeCertificate } from '../api';
import { FileSignature, ShieldAlert, LogOut, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function CollegeDashboard() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({ studentName: '', degree: 'B.S. Computer Science', year: new Date().getFullYear() });
    const [revokeId, setRevokeId] = useState('');

    const [issueStatus, setIssueStatus] = useState(null);
    const [revokeStatus, setRevokeStatus] = useState(null);
    const [loading, setLoading] = useState(false);

    // Issued certificates list (Mocked for UI demo, in a real app this would fetch all certs from node)
    const [recentCerts, setRecentCerts] = useState([]);

    const handleIssue = async (e) => {
        e.preventDefault();
        setLoading(true);
        setIssueStatus(null);
        try {
            const res = await issueCertificate(formData.studentName, formData.degree, formData.year);
            setIssueStatus({ type: 'success', msg: `Success! Tx Hash: ${res.transaction_hash.substring(0, 10)}... | Cert ID: ${res.cert_id}` });
            setRecentCerts([...recentCerts, { ...formData, certId: res.cert_id }]);
            setFormData({ studentName: '', degree: 'B.S. Computer Science', year: new Date().getFullYear() });
        } catch (err) {
            setIssueStatus({ type: 'error', msg: err?.response?.data?.detail || 'Failed to issue certificate.' });
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
            setRevokeStatus({ type: 'success', msg: res.message });
            setRevokeId('');
        } catch (err) {
            setRevokeStatus({ type: 'error', msg: err?.response?.data?.detail || 'Failed to revoke certificate.' });
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/');
    };

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex justify-between items-end border-b border-white/10 pb-6">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400">
                        College Dashboard
                    </h1>
                    <p className="text-neutral-400 mt-1">Manage verifiable student credentials</p>
                </div>
                <button onClick={handleLogout} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-neutral-900 border border-white/10 hover:bg-neutral-800 transition-colors text-sm text-neutral-300 pointer-events-auto">
                    <LogOut className="w-4 h-4" /> Sign Out
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                {/* Issue Certificate Form */}
                <div className="p-6 rounded-2xl bg-neutral-900/50 border border-indigo-500/20 shadow-xl shadow-indigo-500/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 blur-3xl rounded-full" />

                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                            <FileSignature className="w-5 h-5 text-indigo-400" />
                        </div>
                        <h2 className="text-xl font-semibold">Issue Certificate</h2>
                    </div>

                    <form onSubmit={handleIssue} className="space-y-4">
                        <div>
                            <label className="block text-sm text-neutral-400 mb-1">Student Name</label>
                            <input
                                required type="text" value={formData.studentName} onChange={(e) => setFormData({ ...formData, studentName: e.target.value })}
                                className="w-full bg-black/50 border border-white/10 rounded-lg py-2 px-3 focus:outline-none focus:border-indigo-500 transition-colors text-white"
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm text-neutral-400 mb-1">Degree Program</label>
                                <input
                                    required type="text" value={formData.degree} onChange={(e) => setFormData({ ...formData, degree: e.target.value })}
                                    className="w-full bg-black/50 border border-white/10 rounded-lg py-2 px-3 focus:outline-none focus:border-indigo-500 transition-colors text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-neutral-400 mb-1">Graduation Year</label>
                                <input
                                    required type="number" value={formData.year} onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                                    className="w-full bg-black/50 border border-white/10 rounded-lg py-2 px-3 focus:outline-none focus:border-indigo-500 transition-colors text-white"
                                />
                            </div>
                        </div>

                        {issueStatus && (
                            <div className={`p-3 rounded-lg text-sm border ${issueStatus.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
                                {issueStatus.msg}
                            </div>
                        )}

                        <button disabled={loading} type="submit" className="w-full mt-4 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 rounded-lg transition-colors">
                            {loading ? 'Minting on Blockchain...' : 'Sign & Issue Certificate'}
                        </button>
                    </form>
                </div>

                {/* Revoke Certificate Form */}
                <div className="p-6 rounded-2xl bg-neutral-900/50 border border-red-500/20 shadow-xl shadow-red-500/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 blur-3xl rounded-full" />

                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
                            <ShieldAlert className="w-5 h-5 text-red-400" />
                        </div>
                        <h2 className="text-xl font-semibold">Revoke Certificate</h2>
                    </div>

                    <p className="text-sm text-neutral-400 mb-4">
                        Warning: This action writes a permanent revocation state to the blockchain. This cannot be undone.
                    </p>

                    <form onSubmit={handleRevoke} className="space-y-4">
                        <div>
                            <label className="block text-sm text-neutral-400 mb-1">Certificate ID</label>
                            <input
                                required type="text" placeholder="CERT-..." value={revokeId} onChange={(e) => setRevokeId(e.target.value)}
                                className="w-full bg-black/50 border border-white/10 rounded-lg py-2 px-3 focus:outline-none focus:border-red-500 transition-colors text-white font-mono"
                            />
                        </div>

                        {revokeStatus && (
                            <div className={`p-3 rounded-lg text-sm border ${revokeStatus.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
                                {revokeStatus.msg}
                            </div>
                        )}

                        <button disabled={loading} type="submit" className="w-full mt-4 bg-red-600/80 hover:bg-red-500 text-white font-medium py-2 rounded-lg transition-colors">
                            {loading ? 'Executing Revocation...' : 'Revoke Credential'}
                        </button>
                    </form>
                </div>
            </div>

            {/* Recents Widget */}
            {recentCerts.length > 0 && (
                <div className="mt-8 p-6 rounded-2xl bg-neutral-900/30 border border-white/5">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" /> Recently Issued
                    </h3>
                    <div className="space-y-3">
                        {recentCerts.map((c, i) => (
                            <div key={i} className="flex justify-between items-center p-3 rounded-lg bg-black/40 border border-white/5">
                                <div>
                                    <p className="font-medium text-white">{c.studentName} <span className="text-neutral-500 text-sm ml-2">({c.degree}, {c.year})</span></p>
                                    <p className="text-xs text-neutral-400 font-mono mt-1">ID: {c.certId}</p>
                                </div>
                                <button onClick={() => navigate(`/student/${c.certId}`)} className="text-indigo-400 text-sm hover:text-indigo-300 underline">
                                    View Page
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
