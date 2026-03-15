import { ShieldCheck, Search, GraduationCap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Home() {
    const navigate = useNavigate();

    return (
        <div className="min-h-[70vh] flex flex-col items-center justify-center text-center relative px-4">
            <div className="absolute top-0 right-0 w-1/3 h-full pointer-events-none opacity-40 animate-fade-in-up-delay-3 hidden lg:block line-art-network">
                <img src="/assets/blockchain_minimal_network.png" alt="" className="w-full h-auto object-contain" />
            </div>
            <div className="absolute top-1/4 left-0 w-1/4 h-full pointer-events-none opacity-30 animate-fade-in-up-delay-3 hidden lg:block -scale-x-100 line-art-network">
                <img src="/assets/blockchain_minimal_network.png" alt="" className="w-full h-auto object-contain" />
            </div>

            <div className="animate-fade-in-up">
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-slate-600 text-xs font-black uppercase tracking-[0.15em] mb-10 shadow-sm relative z-10">
                    <ShieldCheck className="w-3.5 h-3.5 text-indigo-500" />
                    Distributed Trust Network
                </div>
            </div>

            <h1 className="text-5xl sm:text-7xl font-black tracking-tight text-slate-950 mb-8 animate-fade-in-up-delay-1 leading-[1.05] relative z-10">
                Independent <br />
                <span className="gradient-text">
                    Digital Credentials
                </span>
            </h1>

            <p className="text-lg text-slate-500 max-w-2xl mx-auto mb-14 animate-fade-in-up-delay-2 font-bold leading-relaxed relative z-10">
                Eliminate record tampering with a secure blockchain ecosystem. 
                Instant, verifiable academic history accessible anywhere.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl animate-fade-in-up-delay-3 px-2">
                {/* Verification Portal Card */}
                <div
                    onClick={() => navigate('/verify')}
                    className="group relative p-10 rounded-2xl soft-card soft-card-hover cursor-pointer overflow-hidden transition-all duration-300"
                >
                    <div className="w-14 h-14 rounded-2xl bg-indigo-50 flex items-center justify-center mb-8 border border-indigo-100 shadow-sm group-hover:scale-110 transition-transform">
                        <Search className="w-7 h-7 text-indigo-600" />
                    </div>
                    <h3 className="text-2xl font-black text-slate-950 mb-4 tracking-tight">Verify Certificate</h3>
                    <p className="text-slate-500 text-base leading-relaxed font-bold">Instantly authenticate any graduate credential using its unique tracker ID.</p>
                    <div className="mt-8 flex items-center gap-2 text-indigo-600 font-black text-xs uppercase tracking-widest pt-4 border-t border-slate-50">
                        Go to Verify →
                    </div>
                </div>

                {/* Institutional Access Card */}
                <div
                    onClick={() => navigate('/login')}
                    className="group relative p-10 rounded-2xl soft-card soft-card-hover cursor-pointer overflow-hidden transition-all duration-300"
                >
                    <div className="w-14 h-14 rounded-2xl bg-slate-900 flex items-center justify-center mb-8 border border-slate-800 shadow-sm group-hover:scale-110 transition-transform">
                        <GraduationCap className="w-7 h-7 text-white" />
                    </div>
                    <h3 className="text-2xl font-black text-slate-950 mb-4 tracking-tight">College Login</h3>
                    <p className="text-slate-500 text-base leading-relaxed font-bold">Management tools for universities to securely issue and revoke student records.</p>
                    <div className="mt-8 flex items-center gap-2 text-slate-900 font-black text-xs uppercase tracking-widest pt-4 border-t border-slate-50">
                        Sign In →
                    </div>
                </div>
            </div>
            
            {/* Minimal Stat row - High Contrast */}
            <div className="mt-24 flex flex-wrap justify-center gap-16 border-t border-slate-200 pt-12 w-full max-w-2xl animate-fade-in-up-delay-3">
               <div className="text-center group">
                  <p className="text-3xl font-black text-slate-950 group-hover:text-indigo-600 transition-colors">100%</p>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1">Tamper-Proof</p>
               </div>
               <div className="text-center group">
                  <p className="text-3xl font-black text-slate-950 group-hover:text-indigo-600 transition-colors">Real-Time</p>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1">Verification</p>
               </div>
               <div className="text-center group">
                  <p className="text-3xl font-black text-slate-950 group-hover:text-indigo-600 transition-colors">Direct</p>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1">Access</p>
               </div>
            </div>
        </div>
    );
}
