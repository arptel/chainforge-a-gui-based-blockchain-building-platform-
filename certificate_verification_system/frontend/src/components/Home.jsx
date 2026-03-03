import { ShieldCheck, Search, GraduationCap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Home() {
    const navigate = useNavigate();

    return (
        <div className="min-h-[80vh] flex flex-col items-center justify-center text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm font-medium mb-8">
                <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
                Secured by ChainForge Network
            </div>

            <h1 className="text-6xl sm:text-7xl font-extrabold tracking-tight mb-6">
                The Future of <br />
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-blue-400 to-cyan-400">
                    Academic Verification
                </span>
            </h1>

            <p className="text-lg text-neutral-400 max-w-2xl mx-auto mb-12">
                A decentralized, tamper-proof repository for university degrees.
                Instant verification for employers. Zero fraud.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">
                {/* Employers Card */}
                <div
                    onClick={() => navigate('/verify')}
                    className="group relative p-8 rounded-2xl bg-neutral-900/50 border border-white/10 hover:border-blue-500/50 transition-all cursor-pointer overflow-hidden"
                >
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                        <Search className="w-6 h-6 text-blue-400" />
                    </div>
                    <h3 className="text-2xl font-bold mb-2">For Employers</h3>
                    <p className="text-neutral-400">Verify a candidate's degree instantly using their unique certificate ID.</p>
                </div>

                {/* Colleges Card */}
                <div
                    onClick={() => navigate('/login')}
                    className="group relative p-8 rounded-2xl bg-neutral-900/50 border border-white/10 hover:border-indigo-500/50 transition-all cursor-pointer overflow-hidden"
                >
                    <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                        <GraduationCap className="w-6 h-6 text-indigo-400" />
                    </div>
                    <h3 className="text-2xl font-bold mb-2">For Institutions</h3>
                    <p className="text-neutral-400">Securely issue, revoke, and manage student degrees on the blockchain.</p>
                </div>
            </div>
        </div>
    );
}
