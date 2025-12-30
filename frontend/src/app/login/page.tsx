"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Terminal, Loader2, ArrowRight } from "lucide-react";
import Image from "next/image";

export default function LoginPage() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const { error } = await signIn(email, password);

    if (error) {
      setError(error.message);
      setLoading(false);
    } else {
      router.push("/dashboard");
    }
  };

  return (
    <div className="min-h-screen flex w-full bg-[#050505] text-white font-sans overflow-hidden">

      {/* LEFT: Auth Form */}
      <div className="w-full lg:w-[45%] flex flex-col justify-center px-12 lg:px-24 relative z-10">
        {/* Grid Background */}
        <div className="absolute inset-0 bg-grid-pattern-subtle opacity-50 pointer-events-none" />

        <div className="relative z-20 max-w-sm w-full mx-auto">
          <div className="mb-12">
            <div className="w-10 h-10 bg-blue-500/10 border border-blue-500/20 rounded-md flex items-center justify-center text-blue-500 mb-8 shadow-lg shadow-blue-900/10">
              <Terminal size={20} />
            </div>
            <h1 className="text-4xl lg:text-5xl font-light tracking-tight mb-4 text-white">
              Log in to your <br />
              <span className="text-blue-500">workstation</span>.
            </h1>
            <p className="text-zinc-500 font-light text-lg">
              Enter your credentials to access the sovereign agent dashboard.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-4">
              <div className="group">
                <label className="block text-xs font-mono text-zinc-500 mb-2 uppercase tracking-wider">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  required
                  className="w-full bg-[#09090b] border border-white/10 px-4 py-3 text-base text-white placeholder:text-zinc-700 focus:border-blue-500/50 transition-colors rounded-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-zinc-500 mb-2 uppercase tracking-wider">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-[#09090b] border border-white/10 px-4 py-3 text-base text-white placeholder:text-zinc-700 focus:border-blue-500/50 transition-colors rounded-sm"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 bg-red-950/20 border border-red-900/30 text-red-400 text-sm font-mono rounded-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium py-3.5 rounded-sm disabled:opacity-50 transition-all flex items-center justify-center gap-2 group"
            >
              {loading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <>
                  Access Terminal
                  <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          <p className="mt-8 text-sm text-zinc-600 font-light">
            Don't have an identity yet?{" "}
            <Link href="/signup" className="text-zinc-400 hover:text-blue-400 transition-colors underline decoration-zinc-800 underline-offset-4">
              Initialize here
            </Link>
          </p>
        </div>
      </div>

      {/* RIGHT: Visual / Content */}
      <div className="hidden lg:flex w-[55%] items-center justify-center p-8 bg-[#020202]">

        {/* Bordered Container */}
        <div className="relative w-full h-[98%] max-w-3xl border border-white/10 rounded-sm overflow-hidden flex flex-col justify-end p-12">

          {/* Background Image */}
          <div className="absolute inset-0 z-0">
            <Image
              src="/new-york-ascii.png"
              alt="New York ASCII"
              fill
              className="object-cover object-center scale-110 opacity-60"
              priority
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/20 to-transparent" />
          </div>

          {/* Content Card */}
          <div className="relative z-10 w-full backdrop-blur-md bg-black/40 border border-white/10 p-6 rounded-sm shadow-2xl">
            <div className="space-y-4">
              <p className="text-xl font-light leading-relaxed text-zinc-200">
                "The future of work isn't just about automation. It's about <span className="text-blue-400 font-normal bg-blue-500/10 px-2 py-0.5 rounded-sm">sovereign collaboration</span>."
              </p>
              <div className="flex items-center gap-3 pt-2">
                <div className="w-8 h-8 rounded-full bg-zinc-800 border border-white/10" />
                <div>
                  <p className="text-sm font-medium text-white">Elena Rostova</p>
                  <p className="text-xs text-zinc-500">Director of AI, CyberDyne</p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
