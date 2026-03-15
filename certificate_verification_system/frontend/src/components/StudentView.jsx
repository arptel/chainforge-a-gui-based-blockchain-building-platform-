import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getIssuers } from '../api';
import { SPVLightClient } from '../spv/LightClient';
import { ShieldCheck, Calendar, Share2, Download, CheckCircle2, QrCode, Building, Award, ShieldAlert, Cpu } from 'lucide-react';

// Initial fallback nodes, will be updated dynamically from the backend
const DEFAULT_NODES = ["http://127.0.0.1:8080", "http://127.0.0.1:8081"];

export default function StudentView() {
    const { certId } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loadingStep, setLoadingStep] = useState('Connecting...');
    const [error, setError] = useState('');
    const [statusData, setStatusData] = useState({ isValid: false, status: '', message: '' });
    const [issuersMap, setIssuersMap] = useState({});
    const [spvNode, setSpvNode] = useState(new SPVLightClient(DEFAULT_NODES));
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        const verifyTrustlessly = async () => {
            try {
                setLoadingStep('Connecting...');
                
                // 1. Dynamic Node Discovery
                const issuers = await getIssuers();
                setIssuersMap(issuers);
                
                const dynamicNodes = Object.values(issuers)
                    .map(issuer => issuer.url)
                    .filter(url => !!url);
                
                // Temporarily use local spvNode instance or update current one
                const activeClient = dynamicNodes.length > 0 
                    ? new SPVLightClient(dynamicNodes)
                    : spvNode;
                
                if (dynamicNodes.length > 0) setSpvNode(activeClient);

                // 2. Trustless SPV Flow
                await activeClient.syncHeaders();
                await new Promise(r => setTimeout(r, 650));

                setLoadingStep('Searching...');
                await new Promise(r => setTimeout(r, 650));

                setLoadingStep('Verifying...');
                const verifyRes = await activeClient.verifyCertificate(certId);
                setStatusData(verifyRes);

                if (!verifyRes.isValid && verifyRes.status !== "Revoked") {
                    setError(verifyRes.message || 'Certificate not found.');
                } else {
                    setData(verifyRes.data);
                }
            } catch (err) {
                console.error(err);
                setError('Connection timeout. Please try again.');
            } finally {
                setLoadingStep('');
            }
        };
        verifyTrustlessly();
    }, [certId]);

    const handleShare = () => {
        navigator.clipboard.writeText(window.location.href);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (loadingStep) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-10 animate-in fade-in">
                <div className="relative w-28 h-28 flex items-center justify-center">
                    <div className="absolute inset-0 border-4 border-slate-100 rounded-full shadow-inner"></div>
                    <div className="absolute inset-0 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                    <ShieldCheck className="w-10 h-10 text-slate-300 animate-pulse-soft" />
                </div>
                <div className="text-center space-y-5">
                    <h3 className="text-3xl font-black text-slate-950 tracking-tight">Verifying Certificate</h3>
                    <div className="inline-flex items-center gap-4 bg-slate-900 border border-slate-800 rounded-2xl px-8 py-4 text-indigo-400 font-black text-xs tracking-[0.2em] shadow-2xl">
                        <span className="animate-pulse-soft mr-2">●</span> {loadingStep}
                    </div>
                </div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-8 animate-in zoom-in-95">
                <div className="w-24 h-24 bg-red-50 rounded-[2.5rem] flex items-center justify-center mb-10 border border-red-200 shadow-sm animate-shake">
                    <ShieldAlert className="w-12 h-12 text-red-600" />
                </div>
                <h2 className="text-4xl font-black text-slate-950 mb-4 tracking-tighter leading-tight">Verification Failed</h2>
                <p className="text-slate-500 max-w-sm mx-auto mb-12 font-bold text-base leading-relaxed">{error || "This certificate could not be verified in our records."}</p>
                <button onClick={() => navigate('/')} className="btn-secondary px-12 py-5 rounded-2xl text-white font-black transition-all shadow-xl active:scale-95 uppercase tracking-widest text-xs">Home</button>
            </div>
        );
    }

    return (
        <div className="max-w-5xl mx-auto py-6 space-y-10 animate-in fade-in slide-in-from-bottom-12 duration-1000">
            {/* Minimal Toolbar */}
            <div className="flex flex-col sm:flex-row justify-between items-center gap-6 bg-white border border-slate-200 rounded-[2rem] px-8 py-4 shadow-xl shadow-slate-100">
                <div className="flex items-center gap-5">
                   <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800">
                        <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_10px_#10b981] animate-pulse" />
                        <span className="text-[11px] uppercase tracking-[0.2em] font-black text-white">Verified Account</span>
                    </div>
                </div>
                <div className="flex items-center gap-8">
                    <button onClick={handleShare} className="flex items-center gap-2 text-xs font-black text-indigo-600 uppercase tracking-[0.2em] hover:text-indigo-700 transition-colors">
                        {copied ? <CheckCircle2 className="w-5 h-5" /> : <Share2 className="w-5 h-5" />}
                        {copied ? 'Link Copied' : 'Share Certificate'}
                    </button>
                    <div className="h-6 w-px bg-slate-100" />
                    <button className="flex items-center gap-2 text-xs font-black text-slate-400 uppercase tracking-[0.2em] hover:text-slate-900 transition-colors">
                        <Download className="w-5 h-5" />
                        Download PDF
                    </button>
                </div>
            </div>

            {/* Certificate Display */}
            <div className="relative p-2 rounded-[3.5rem] bg-indigo-600 shadow-[0_48px_120px_-32px_rgba(30,41,59,0.2)]">
                <div className="relative bg-white p-14 md:p-28 rounded-[3.25rem] border-[1px] border-white/50 mx-auto overflow-hidden">
                    
                    {/* Security Watermarks */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-[0.02] pointer-events-none select-none">
                        <ShieldCheck className="w-[45rem] h-[45rem]" />
                    </div>
                    
                    {/* Elegant Slate Borders */}
                    <div className="absolute inset-6 border-[1px] border-slate-100 pointer-events-none rounded-[2.5rem]" />
                    <div className="absolute inset-8 border-[6px] border-slate-50 pointer-events-none rounded-[2.25rem]" />
                    <div className="absolute inset-[3.5rem] border-[1px] border-slate-50 pointer-events-none rounded-[1.75rem]" />

                    {/* Content */}
                    <div className="relative z-10 text-center">
                        <div className="flex justify-center items-center gap-6 mb-16">
                            <img src="/assets/blockchain_simple_trust_badge.png" alt="" className="w-16 h-16 opacity-80" />
                            {statusData.isValid ? (
                                <div className="inline-flex items-center gap-3 px-8 py-3 rounded-full bg-slate-900 border-2 border-slate-800 text-indigo-400 font-black tracking-[0.4em] text-[11px] shadow-2xl">
                                    <ShieldCheck className="w-5 h-5" /> VALID CERTIFICATE
                                </div>
                            ) : (
                                <div className="inline-flex items-center gap-3 px-8 py-3 rounded-full bg-red-600 text-white font-black tracking-[0.4em] text-[11px] shadow-2xl">
                                    <ShieldAlert className="w-5 h-5" /> REVOKED
                                </div>
                            )}
                        </div>

                        <div className="uppercase tracking-[0.6em] text-slate-300 text-[11px] font-black mb-12 flex items-center justify-center gap-6">
                           <div className="h-px w-16 bg-slate-100" />
                           OFFICIAL CERTIFICATE VIEW
                           <div className="h-px w-16 bg-slate-100" />
                        </div>

                        <h1 className="text-6xl md:text-8xl font-serif text-slate-950 tracking-tight italic mb-24 px-4 leading-tight">
                            Digital Diploma
                        </h1>

                        <div className="space-y-24">
                            <div className="space-y-6">
                                <p className="text-2xl text-slate-400 italic font-serif">Awarded To</p>
                                <h2 className="text-6xl md:text-8xl font-black text-slate-950 tracking-tighter pb-4 underline underline-offset-[16px] decoration-slate-100 decoration-4">
                                    {data.student_name}
                                </h2>
                            </div>

                            <div className="space-y-6">
                                <p className="text-2xl text-slate-400 italic font-serif">For completing the degree of</p>
                                <h3 className="text-4xl md:text-5xl font-black text-slate-800 tracking-tight leading-snug">{data.degree}</h3>
                            </div>
                        </div>

                        {/* Signature/Validation Section */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-20 mt-32 pt-20 border-t-2 border-slate-50 group">
                            <div className="text-left space-y-10">
                                <div className="space-y-4">
                                    <span className="text-[11px] text-slate-400 uppercase font-black tracking-[0.3em] block">College / University</span>
                                    <div className="flex items-start gap-4">
                                        <Building className="w-6 h-6 text-slate-900 mt-1" />
                                        <div>
                                            <p className="text-xl font-black text-slate-950 leading-tight tracking-tight">{issuersMap[data.issuer_id]?.name || "Academic Institution"}</p>
                                            <p className="text-[10px] font-mono text-slate-300 mt-2.5 break-all tracking-tighter leading-relaxed">{data.issuer_id}</p>
                                        </div>
                                    </div>
                                </div>
                                <div>
                                    <span className="text-[11px] text-slate-400 uppercase font-black tracking-[0.3em] block mb-2">Year Issued</span>
                                    <p className="text-2xl font-black text-slate-950 tracking-widest">{data.year}</p>
                                </div>
                            </div>

                            <div className="flex flex-col items-center justify-center">
                                <div className="p-6 bg-slate-50 rounded-3xl border-2 border-slate-100 shadow-inner group-hover:scale-110 transition-transform duration-500">
                                    <QrCode className="w-20 h-20 text-slate-950" strokeWidth={1} />
                                </div>
                                <span className="text-[9px] text-slate-400 uppercase mt-6 font-black tracking-[0.4em] opacity-40">Certificate ID: {certId.slice(0, 8)}</span>
                            </div>

                            <div className="text-right space-y-10 flex flex-col items-end">
                                <div className="max-w-[220px]">
                                    <span className="text-[11px] text-slate-400 uppercase font-black tracking-[0.3em] block mb-4">Verification ID</span>
                                    <div className="p-3 bg-slate-950 rounded-2xl text-[10px] font-mono text-indigo-400 break-all leading-loose text-left shadow-2xl">
                                        {certId}
                                    </div>
                                </div>
                                <div className="pt-4 flex items-center gap-4">
                                    <span className="text-[10px] text-slate-400 uppercase font-black tracking-[0.3em]">Verified Record</span>
                                    <CheckCircle2 className="w-10 h-10 text-emerald-500/10 fill-emerald-50" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer Disclaimer */}
            <div className="text-center px-10 pb-16">
                <p className="text-[11px] text-slate-400 max-w-2xl mx-auto leading-relaxed font-black uppercase tracking-[0.2em] opacity-80">
                    Sovereign Digital Certificate <br />
                    <span className="text-slate-300 text-[10px]">This is an official digital record. Modifications to this view do not alter the underlying blockchain record.</span>
                </p>
            </div>
        </div>
    );
}
