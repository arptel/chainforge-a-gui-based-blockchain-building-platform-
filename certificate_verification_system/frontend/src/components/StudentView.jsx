import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getIssuers } from '../api';
import { SPVLightClient } from '../spv/LightClient';
import { ShieldCheck, Calendar, User, Award, ShieldAlert, Cpu } from 'lucide-react';

// Instantiate SPV Light Node globally for this session
const spvNode = new SPVLightClient(["http://127.0.0.1:8080", "http://127.0.0.1:8081"]);

export default function StudentView() {
    const { certId } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loadingStep, setLoadingStep] = useState('Initializing SPV Light Node...');
    const [error, setError] = useState('');
    const [statusData, setStatusData] = useState({ isValid: false, status: '', message: '' });
    const [issuersMap, setIssuersMap] = useState({});

    useEffect(() => {
        const verifyTrustlessly = async () => {
            try {
                // Step 1: Connect to the network
                setLoadingStep('Synchronizing Block Headers via P2P...');
                await spvNode.syncHeaders();

                // Optional delay to let user see SPV is working!
                await new Promise(r => setTimeout(r, 600));

                // Step 2: Request Proof
                setLoadingStep('Requesting Cryptographic Merkle Proof...');
                await new Promise(r => setTimeout(r, 600));

                // Step 3: Mathmatically verify
                setLoadingStep('Mathematically Verifying Hash Integrity...');
                const verifyRes = await spvNode.verifyCertificate(certId);
                setStatusData(verifyRes);

                if (verifyRes.isValid || verifyRes.status === "Revoked") {
                    // The data is now guaranteed authentic directly from the SPV check! 
                    setData(verifyRes.data);

                    try {
                        const map = await getIssuers();
                        setIssuersMap(map);
                    } catch (err) {
                        console.error("Failed to load issuer map:", err);
                    }
                } else {
                    setError(verifyRes.message || 'Certificate not found on the blockchain.');
                }
            } catch (err) {
                console.error(err);
                setError(err.message || 'Failed to sync with the decentralized network.');
            } finally {
                setLoadingStep('');
            }
        };
        verifyTrustlessly();
    }, [certId]);

    if (loadingStep) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
                <div className="relative w-24 h-24 flex items-center justify-center">
                    <div className="absolute inset-0 border-4 border-indigo-500/30 rounded-full"></div>
                    <div className="absolute inset-0 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                    <Cpu className="w-8 h-8 text-indigo-400 animate-pulse" />
                </div>
                <div className="text-center">
                    <h3 className="text-xl font-bold text-white mb-2">Web3 Verification in Progress</h3>
                    <p className="text-indigo-300 font-mono text-sm tracking-wide bg-indigo-500/10 px-4 py-2 rounded-lg border border-indigo-500/20 shadow-inner">
                        <span className="animate-pulse mr-2">▶</span>
                        {loadingStep}
                    </p>
                </div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
                <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mb-4">
                    <ShieldAlert className="w-8 h-8 text-red-500" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Invalid Certificate Link</h2>
                <p className="text-neutral-400">{error}</p>
                <button onClick={() => navigate('/')} className="mt-6 text-indigo-400 hover:text-indigo-300">Return Home</button>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto py-8">
            {/* Decorative Document Wrapper */}
            <div className="relative p-1 rounded-[2rem] bg-gradient-to-br from-indigo-500/20 via-blue-500/10 to-transparent shadow-2xl">
                <div className="relative bg-neutral-950 p-8 md:p-16 rounded-[1.85rem] border border-white/5 mx-auto overflow-hidden">

                    {/* Watermark */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-5 pointer-events-none">
                        <ShieldCheck className="w-[30rem] h-[30rem]" />
                    </div>

                    {/* Certificate Content */}
                    <div className="relative z-10 text-center space-y-8">
                        <div className="flex justify-center mb-8">
                            {statusData.isValid ? (
                                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-medium tracking-wide shadow-[0_0_15px_rgba(52,211,153,0.1)]">
                                    <ShieldCheck className="w-5 h-5" />
                                    <span>TRUSTLESS SPV VALIDATION: SUCCESS</span>
                                </div>
                            ) : (
                                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 font-medium tracking-wide">
                                    <ShieldAlert className="w-5 h-5" /> CERTIFICATE REVOKED
                                </div>
                            )}
                        </div>

                        <div className="space-y-2 uppercase tracking-widest text-neutral-400 text-sm font-bold">
                            ChainForge Network <br /> College / University
                        </div>

                        <h1 className="text-5xl md:text-6xl font-serif text-white tracking-wide py-4 border-y border-white/10 my-10">
                            Certificate of Degree
                        </h1>

                        <p className="text-lg text-neutral-300 italic">This certifies that</p>
                        <h2 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white via-indigo-100 to-white pb-2">
                            {data.student_name}
                        </h2>

                        <p className="text-lg text-neutral-300 italic">has successfully completed the requirements for the degree of</p>
                        <h3 className="text-3xl font-medium text-blue-400">{data.degree}</h3>

                        <div className="grid grid-cols-2 gap-8 max-w-lg mx-auto mt-16 pt-8 border-t border-white/5">
                            <div className="text-left">
                                <span className="text-xs text-neutral-500 uppercase tracking-widest block mb-1">Graduation Year</span>
                                <p className="text-xl font-mono text-white">{data.year}</p>
                            </div>
                            <div className="text-left">
                                <span className="text-xs text-neutral-500 uppercase tracking-widest block mb-1">Blockchain Tracking ID</span>
                                <p className="text-sm font-mono text-neutral-400 truncate">{certId}</p>
                            </div>
                        </div>

                        <div className="mt-8 text-center bg-white/5 p-4 rounded-xl border border-white/5 inline-block min-w-[50%]">
                            <span className="text-xs text-indigo-400 uppercase tracking-widest block mb-1 font-semibold">Cryptographically Signed & Verified</span>
                            <p className="text-lg font-medium text-white mb-1">{issuersMap[data.issuer_id] || "Unknown College"}</p>
                            <p className="text-xs font-mono text-neutral-500 truncate" title={data.issuer_id}>{data.issuer_id}</p>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
}

