import { useState } from 'react';
import { verifyCertificate, getCertificate } from '../api';
import { Search, BadgeCheck, XCircle, AlertTriangle, Calendar, Award, User, Building } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function CompanyDashboard() {
    const [certId, setCertId] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [certData, setCertData] = useState(null);
    const navigate = useNavigate();

    const handleVerify = async (e) => {
        e.preventDefault();
        if (!certId) return;

        setLoading(true);
        setResult(null);
        setCertData(null);
        try {
            const { is_valid, status, message } = await verifyCertificate(certId);
            setResult({ isValid: is_valid, status, message });

            // If valid, optionally fetch details
            if (is_valid) {
                const payload = await getCertificate(certId);
                setCertData(payload.data);
            }

        } catch (err) {
            setResult({ isValid: false, status: 'Error', message: 'Unable to connect to blockchain node' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-3xl mx-auto min-h-[70vh] flex flex-col items-center justify-center animate-in fade-in slide-in-from-bottom-4 duration-500">

            <div className="w-16 h-16 rounded-2xl bg-blue-500/10 flex items-center justify-center mb-6 shadow-lg shadow-blue-500/20">
                <Search className="w-8 h-8 text-blue-400" />
            </div>

            <h1 className="text-4xl font-bold mb-4 text-center">Company Verification Gateway</h1>
            <p className="text-neutral-400 text-center mb-10 max-w-lg">
                Enter a Blockchain Certificate ID to verify a candidate's academic credentials directly from the decentralized registry.
            </p>

            <form onSubmit={handleVerify} className="w-full relative mb-12">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Search className="h-5 w-5 text-neutral-500" />
                </div>
                <input
                    type="text"
                    value={certId}
                    onChange={(e) => setCertId(e.target.value)}
                    placeholder="e.g. CERT-A1B2C3D4"
                    className="block w-full pl-12 pr-32 py-4 bg-neutral-900/80 border border-white/10 rounded-2xl text-lg text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all font-mono"
                />
                <div className="absolute inset-y-2 right-2 flex items-center">
                    <button
                        type="submit"
                        disabled={loading}
                        className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-colors disabled:opacity-50"
                    >
                        {loading ? 'Querying...' : 'Verify'}
                    </button>
                </div>
            </form>

            {/* Result Display */}
            {result && (
                <div className={`w-full p-8 rounded-2xl border backdrop-blur-sm transition-all animate-in zoom-in-95 duration-300 ${result.isValid
                        ? 'bg-emerald-950/30 border-emerald-500/30 shadow-[0_0_50px_-12px_rgba(16,185,129,0.3)]'
                        : 'bg-red-950/30 border-red-500/30 shadow-[0_0_50px_-12px_rgba(239,68,68,0.3)]'
                    }`}>
                    <div className="flex items-start gap-4">
                        <div className="mt-1">
                            {result.isValid ? (
                                <BadgeCheck className="w-8 h-8 text-emerald-400" />
                            ) : result.status === 'Revoked' ? (
                                <AlertTriangle className="w-8 h-8 text-red-500" />
                            ) : (
                                <XCircle className="w-8 h-8 text-red-400" />
                            )}
                        </div>
                        <div className="flex-1">
                            <h3 className={`text-2xl font-bold mb-1 ${result.isValid ? 'text-emerald-400' : 'text-red-400'}`}>
                                {result.status}
                            </h3>
                            <p className="text-neutral-300 font-mono text-sm mb-4">ID: {certId}</p>
                            <p className="text-neutral-400">{result.message}</p>

                            {certData && result.isValid && (
                                <div className="mt-6 pt-6 border-t border-white/10 grid grid-cols-2 gap-y-4 gap-x-8">
                                    <div>
                                        <span className="text-xs text-emerald-500/70 font-bold uppercase tracking-wider mb-1 block flex items-center gap-1"><User className="w-3 h-3" /> Candidate Name</span>
                                        <p className="text-lg font-medium text-white">{certData.student_name}</p>
                                    </div>
                                    <div>
                                        <span className="text-xs text-emerald-500/70 font-bold uppercase tracking-wider mb-1 block flex items-center gap-1"><Award className="w-3 h-3" /> Degree</span>
                                        <p className="text-lg font-medium text-white">{certData.degree}</p>
                                    </div>
                                    <div>
                                        <span className="text-xs text-emerald-500/70 font-bold uppercase tracking-wider mb-1 block flex items-center gap-1"><Calendar className="w-3 h-3" /> Graduation Year</span>
                                        <p className="text-lg font-medium text-white">{certData.year}</p>
                                    </div>
                                    <div>
                                        <span className="text-xs text-emerald-500/70 font-bold uppercase tracking-wider mb-1 block flex items-center gap-1"><Building className="w-3 h-3" /> Issuing Authority</span>
                                        <p className="text-lg font-medium text-white font-mono text-sm break-all">{certData.issuer_id}</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
