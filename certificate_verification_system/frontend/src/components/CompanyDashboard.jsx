import { useState, useEffect } from 'react';
import { getIssuers } from '../api';
import { SPVLightClient } from '../spv/LightClient';
import { Search, BadgeCheck, XCircle, AlertTriangle, Calendar, Award, User, Building, ExternalLink, ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// Initial fallback nodes, will be updated dynamically from the backend
const DEFAULT_NODES = ["http://127.0.0.1:8080", "http://127.0.0.1:8081"];

export default function CompanyDashboard() {
    const [certId, setCertId] = useState('');
    const [data, setData] = useState(null);
    const [loadingStep, setLoadingStep] = useState('');
    const [error, setError] = useState('');
    const [statusData, setStatusData] = useState({ isValid: false, status: '', message: '' });
    const [issuersMap, setIssuersMap] = useState({});
    const [spvNode, setSpvNode] = useState(new SPVLightClient(DEFAULT_NODES));
    const navigate = useNavigate();

    useEffect(() => {
        const initPortal = async () => {
            try {
                const map = await getIssuers();
                setIssuersMap(map);
                
                // Extract all unique node URLs from the issuer map
                const dynamicNodes = Object.values(map)
                    .map(issuer => issuer.url)
                    .filter(url => !!url);
                
                if (dynamicNodes.length > 0) {
                    console.log("[Portal] Discovered dynamic nodes:", dynamicNodes);
                    setSpvNode(new SPVLightClient(dynamicNodes));
                }
            } catch (err) {
                console.error("Failed to initialize discovery:", err);
            }
        };
        initPortal();
    }, []);

    const handleVerify = async (e) => {
        if (e) e.preventDefault();
        if (!certId) return;

        setData(null);
        setError('');
        setStatusData({ isValid: false, status: '', message: '' });

        try {
            setLoadingStep('Connecting...');
            await spvNode.syncHeaders();
            await new Promise(r => setTimeout(r, 600));

            setLoadingStep('Searching...');
            await new Promise(r => setTimeout(r, 600));

            setLoadingStep('Verifying...');
            const verifyRes = await spvNode.verifyCertificate(certId);
            setStatusData(verifyRes);

            if (verifyRes.isValid || verifyRes.status === "Revoked") {
                setData(verifyRes.data);
                // Issuers already loaded in useEffect, but refresh map just in case to show name
                try {
                    const map = await getIssuers();
                    setIssuersMap(map);
                } catch (err) {
                    console.error("Failed to update issuer map:", err);
                }
            } else {
                setError(verifyRes.message || 'Certificate not found.');
            }
        } catch (err) {
            console.error(err);
            setError('Connection error. Please try again.');
        } finally {
            setLoadingStep('');
        }
    };

    return (
        <div className="max-w-6xl mx-auto space-y-14 relative p-4">
            {/* Subtle background pattern */}
            <div className="absolute inset-0 bg-blockchain-pattern pointer-events-none -z-10 rounded-[3rem]"></div>

            <div className="text-center space-y-6">
                <div className="inline-flex items-center gap-3 px-5 py-2 rounded-full bg-slate-900 border border-slate-800 text-white text-[10px] font-black uppercase tracking-[0.25em] mb-4 shadow-xl shadow-slate-200">
                    <ShieldCheck className="w-4 h-4 text-indigo-400" /> Verification Portal
                </div>
                <h1 className="text-5xl md:text-6xl font-black text-slate-950 tracking-tighter leading-tight">Verify Certificate</h1>
                <p className="text-slate-500 max-w-xl mx-auto leading-relaxed font-bold tracking-tight text-lg">
                    Check the validity of any certificate instantly and securely.
                </p>
            </div>

            {/* Verification Control Area */}
            <div className="soft-card p-3 shadow-[0_32px_64px_-12px_rgba(15,23,42,0.12)] max-w-2xl mx-auto animate-fade-in-up border-slate-200">
                <form onSubmit={handleVerify} className="flex gap-4">
                    <div className="relative flex-1 group">
                        <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-300 group-focus-within:text-indigo-600 transition-colors" />
                        <input
                            type="text"
                            placeholder="Enter Certificate ID (CERT-...)"
                            value={certId}
                            onChange={(e) => setCertId(e.target.value)}
                            className="slate-input w-full rounded-xl py-5 pl-14 pr-4 font-black tracking-widest text-sm uppercase placeholder:text-slate-300 placeholder:normal-case placeholder:tracking-tight border-none"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={!!loadingStep || !certId}
                        className="btn-primary px-12 rounded-xl transition-all shadow-lg active:scale-95 disabled:opacity-40 uppercase tracking-widest text-xs font-black"
                    >
                        {loadingStep ? 'Verifying...' : 'Verify'}
                    </button>
                </form>
            </div>

            {loadingStep ? (
                <div className="soft-card p-20 text-center space-y-10 animate-in zoom-in-95 duration-500 border-indigo-100">
                    <div className="relative w-24 h-24 mx-auto">
                        <div className="absolute inset-0 border-[6px] border-slate-50 rounded-full shadow-inner"></div>
                        <div className="absolute inset-0 border-[6px] border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                    </div>
                    <div className="space-y-4">
                        <p className="text-3xl font-black text-slate-950 tracking-tight">Checking Database</p>
                        <div className="inline-flex items-center gap-4 bg-slate-900 border border-slate-800 rounded-2xl px-8 py-4 text-indigo-400 font-black text-xs tracking-[0.2em] shadow-2xl">
                            <span className="animate-pulse-soft">●</span> {loadingStep}
                        </div>
                    </div>
                </div>
            ) : error ? (
                <div className="soft-card p-14 border-red-200 bg-red-50 text-center space-y-6 animate-in fade-in">
                    <div className="w-20 h-20 bg-red-100 rounded-3xl flex items-center justify-center mx-auto shadow-sm border border-red-200 animate-shake">
                        <XCircle className="w-12 h-12 text-red-600" />
                    </div>
                    <div className="space-y-3">
                        <h3 className="text-3xl font-black text-slate-950 tracking-tight">Check Failed</h3>
                        <p className="text-red-700 font-bold max-w-md mx-auto text-sm leading-relaxed">{error}</p>
                    </div>
                    <button onClick={() => setError('')} className="text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-slate-900 transition-colors">Dismiss</button>
                </div>
            ) : data ? (
                <div className="relative animate-in zoom-in-95 duration-700">
                    {!statusData.isValid && (
                        <div className="absolute inset-0 z-50 flex items-center justify-center pointer-events-none rounded-[3rem] bg-slate-950/20 backdrop-blur-[2px]">
                            <div className="border-[14px] border-red-600 px-20 py-10 rounded-[2.5rem] bg-white text-red-600 font-black text-7xl uppercase tracking-tighter -rotate-12 shadow-[0_48px_96px_-16px_rgba(220,38,38,0.4)]">
                                REVOKED
                            </div>
                        </div>
                    )}

                    <div className="soft-card overflow-hidden shadow-[0_48px_96px_-24px_rgba(15,23,42,0.15)] relative border-slate-200 bg-white">
                        <div className={`h-3 w-full ${statusData.isValid ? 'bg-indigo-600' : 'bg-red-600'} shadow-sm`} />
                        
                        <div className="p-12 md:p-20 space-y-16">
                            <div className="flex justify-center">
                                {statusData.isValid ? (
                                    <div className="inline-flex items-center gap-4 px-8 py-3 rounded-full bg-slate-900 border-2 border-slate-800 text-indigo-400 font-black tracking-[0.3em] text-[10px] shadow-2xl">
                                        <BadgeCheck className="w-5 h-5" /> VALID CERTIFICATE
                                    </div>
                                ) : (
                                    <div className="inline-flex items-center gap-4 px-8 py-3 rounded-full bg-red-600 text-white font-black tracking-[0.3em] text-[10px] shadow-2xl">
                                        <AlertTriangle className="w-5 h-5" /> REVOKED
                                    </div>
                                )}
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-14">
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] block ml-1">Student Name</label>
                                    <div className="flex items-center gap-4 p-5 rounded-2xl bg-slate-50 border border-slate-100 shadow-inner">
                                        <div className="w-12 h-12 rounded-xl bg-white flex items-center justify-center shadow-sm"><User className="w-6 h-6 text-slate-900" /></div>
                                        <p className="text-2xl font-black text-slate-950 tracking-tight">{data.student_name}</p>
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] block ml-1">Degree</label>
                                    <div className="flex items-center gap-4 p-5 rounded-2xl bg-slate-50 border border-slate-100 shadow-inner">
                                        <div className="w-12 h-12 rounded-xl bg-white flex items-center justify-center shadow-sm"><Award className="w-6 h-6 text-indigo-600" /></div>
                                        <p className="text-xl font-black text-slate-950 tracking-tight leading-tight">{data.degree}</p>
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em] block ml-1">College</label>
                                    <div className="flex items-center gap-4 p-5 rounded-2xl bg-slate-50 border border-slate-100 shadow-inner">
                                        <div className="w-12 h-12 rounded-xl bg-white flex items-center justify-center shadow-sm"><Building className="w-6 h-6 text-indigo-900" /></div>
                                        <p className="text-lg font-black text-slate-950 truncate leading-tight" title={data.issuer_id}>
                                            {issuersMap[data.issuer_id]?.name || "Academic Institution"}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="pt-12 border-t border-slate-100 flex flex-col sm:flex-row justify-between items-center gap-10">
                                <div className="flex items-center gap-4 text-slate-400 font-black text-xs uppercase tracking-widest">
                                    <Calendar className="w-6 h-6 text-slate-200" />
                                    <span>Year: <span className="text-slate-950 font-black bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100 ml-2">{data.year}</span></span>
                                </div>
                                
                                <div className="flex gap-6">
                                    <button 
                                        onClick={() => navigate(`/student/${certId}`)}
                                        className="group flex items-center gap-3 px-10 py-5 rounded-2xl bg-slate-950 text-white font-black transition-all active:scale-95 shadow-2xl shadow-slate-300 text-xs uppercase tracking-widest"
                                    >
                                        <ExternalLink className="w-5 h-5 text-indigo-400 group-hover:scale-110 transition-transform" /> View Certificate
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            ) : null}
            
            <div className="text-center">
                 <p className="text-[9px] font-black text-slate-300 uppercase tracking-[0.4em] max-w-lg mx-auto leading-relaxed">
                    Certificate Verification System <br />
                    ID: <span className="text-slate-400 select-all">{certId || "N/A"}</span>
                 </p>
            </div>
        </div>
    );
}
