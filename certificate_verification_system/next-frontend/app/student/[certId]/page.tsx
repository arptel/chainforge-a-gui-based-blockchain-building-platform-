"use client";

import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { getCertificate, verifyCertificate } from '@/lib/api';
import { ShieldCheck, Calendar, User, Award, ShieldAlert } from 'lucide-react';

export default function StudentView({ params }: { params: Promise<{ certId: string }> }) {
    const { certId } = use(params);
    const router = useRouter();

    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [isValid, setIsValid] = useState(true);

    useEffect(() => {
        const fetchCert = async () => {
            try {
                const verifyRes = await verifyCertificate(certId);
                setIsValid(verifyRes.is_valid);

                if (verifyRes.is_valid || verifyRes.status === "Revoked") {
                    const payload = await getCertificate(certId);
                    setData(payload.data);
                } else {
                    setError('Certificate not found on the blockchain.');
                }
            } catch (err) {
                setError('Error reading from blockchain node.');
            } finally {
                setLoading(false);
            }
        };
        fetchCert();
    }, [certId]);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
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
                <button onClick={() => router.push('/')} className="mt-6 text-indigo-400 hover:text-indigo-300">Return Home</button>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto py-8">
            {/* Decorative Document Wrapper */}
            <div className="relative p-1 rounded-[2rem] bg-gradient-to-br from-indigo-500/20 via-blue-500/10 to-transparent">
                <div className="relative bg-neutral-950 p-8 md:p-16 rounded-[1.85rem] border border-white/5 mx-auto overflow-hidden">

                    {/* Watermark */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-5 pointer-events-none">
                        <ShieldCheck className="w-[30rem] h-[30rem]" />
                    </div>

                    {/* Certificate Content */}
                    <div className="relative z-10 text-center space-y-8">
                        <div className="flex justify-center mb-8">
                            {isValid ? (
                                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-medium">
                                    <ShieldCheck className="w-5 h-5" /> Blockchain Verified Authentic
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

                        <div className="mt-8 text-center">
                            <span className="text-xs text-neutral-600 block mb-1">Signed by Authority</span>
                            <p className="text-xs font-mono text-neutral-500 truncate">{data.issuer_id}</p>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
}
