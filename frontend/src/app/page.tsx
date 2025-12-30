"use client";

import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/lib/auth";
import {
  Terminal,
  Cpu,
  Zap,
  Globe,
  Shield,
  Code2,
  Fingerprint,
  LayoutGrid,
  ArrowRight,
  Plane
} from "lucide-react";

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-[#050505] text-white font-sans overflow-x-hidden flex flex-col selection:bg-yellow-500/30">

      {/* Background Grid */}
      <div className="fixed inset-0 z-0 pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(to right, #80808012 1px, transparent 1px), linear-gradient(to bottom, #80808012 1px, transparent 1px)',
          backgroundSize: '24px 24px'
        }}
      />

      {/* Navbar */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#050505]/80 backdrop-blur-md border-b border-white/5 h-16">
        <div className="container mx-auto px-6 h-full flex items-center justify-between">
          <div className="flex items-center gap-12">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-8 h-8 bg-white rounded-sm flex items-center justify-center text-black font-bold text-xl group-hover:scale-95 transition-transform">
                <Terminal size={18} strokeWidth={3} />
              </div>
            </Link>
            <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-400">
              <Link href="#" className="hover:text-white transition-colors">Sessions API</Link>
              <Link href="#" className="hover:text-white transition-colors">Pricing</Link>
              <Link href="#" className="hover:text-white transition-colors">Blog</Link>
              <Link href="#" className="hover:text-white transition-colors">Docs</Link>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            {user ? (
              <Link href="/dashboard" className="text-sm font-medium text-white hover:text-zinc-300 transition-colors">
                Dashboard
              </Link>
            ) : (
              <Link
                href="/login"
                className="text-sm font-medium bg-white/5 hover:bg-white/10 px-4 py-2 rounded-sm border border-white/10 transition-colors"
              >
                Log in / Sign Up
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="pt-32 pb-20 relative z-10 flex-1">
        <div className="container mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">

          {/* Left: Content */}
          <div className="max-w-xl space-y-8">
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-semibold tracking-tighter leading-[1] text-white">
              Browser Infrastructure <br />
              for AI Agents
            </h1>
            <p className="text-lg text-zinc-400 leading-relaxed max-w-md font-light">
              Ghost is an open-source browser API that lets you control fleets of browsers in the cloud.
            </p>
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link
                href="/signup"
                className="px-8 py-3.5 bg-[#FFE700] hover:bg-[#E6D000] text-black font-bold rounded-sm transition-transform active:scale-95 text-sm uppercase tracking-wide"
              >
                Start For Free
              </Link>
              <Link
                href="#"
                className="px-8 py-3.5 bg-[#111] border border-white/10 hover:border-white/20 text-white font-medium rounded-sm transition-colors text-sm uppercase tracking-wide"
              >
                Read Docs
              </Link>
            </div>
          </div>

          {/* Right: Visual */}
          <div className="relative h-[500px] w-full flex items-center justify-center select-none">
            {/* Blue ASCII Background */}
            <div className="absolute inset-0 z-0 overflow-hidden rounded-lg border border-white/10 bg-[#001524]">
              <Image
                src="/beach-sunset-ascii.png"
                alt="ASCII Visualization"
                fill
                className="object-cover opacity-80 mix-blend-luminosity scale-110 contrast-125"
              />
              <div className="absolute inset-0 bg-blue-900/40 mix-blend-overlay" />
            </div>

            {/* Floating Windows (The "Comparison" Graphic) */}
            <div className="absolute inset-x-8 inset-y-12 z-10 grid grid-cols-2 gap-6 items-center">

              {/* Card 1: Code / Logic */}
              <div className="bg-[#0A0A0A] border border-white/10 rounded-lg shadow-2xl overflow-hidden self-end translate-y-8 -rotate-1 relative z-20 hover:rotate-0 transition-transform duration-500">
                <div className="bg-[#151515] px-4 py-2 flex items-center gap-2 border-b border-white/5">
                  <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/20" />
                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20" />
                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/20" />
                  </div>
                  <div className="text-[10px] font-mono text-zinc-500 ml-2">my_app.py</div>
                </div>
                <div className="p-4 space-y-3 font-mono text-xs">
                  <div className="flex gap-2">
                    <span className="text-purple-400">def</span>
                    <span className="text-blue-400">find_fights</span>():
                  </div>
                  <div className="pl-4 text-zinc-400">
                    goal = <span className="text-green-400">"SFO to NYC"</span>
                  </div>
                  <div className="pl-4 text-zinc-400">
                    browser.goto(<span className="text-green-400">"kayak.com"</span>)
                  </div>
                  <div className="pl-4 text-zinc-400">
                    <span className="text-zinc-500"># AI navigates UI...</span>
                  </div>
                </div>
                <div className="absolute inset-0 bg-black/50 backdrop-blur-[1px]" />
                <div className="absolute bottom-4 left-4 right-4 bg-zinc-900 p-3 rounded border border-white/10 shadow-lg">
                  <div className="flex items-center gap-2 text-white text-xs font-medium mb-1">
                    <Plane size={12} /> Flight Found
                  </div>
                  <div className="text-[10px] text-zinc-400">SFO → JFK • $250</div>
                </div>
              </div>

              {/* Card 2: Browser / Visual */}
              <div className="bg-[#0A0A0A] border border-white/10 rounded-lg shadow-2xl overflow-hidden self-start -translate-y-8 rotate-2 relative z-10 hover:rotate-0 transition-transform duration-500 h-[220px]">
                <div className="bg-[#151515] px-4 py-2 flex items-center justify-between border-b border-white/5">
                  <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
                    <div className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
                    <div className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
                  </div>
                  <div className="bg-black/50 px-2 py-0.5 rounded text-[10px] text-zinc-500 font-mono">
                    kayak.com
                  </div>
                </div>
                <div className="p-6 relative h-full">
                  {/* Mock UI */}
                  <div className="space-y-4 opacity-50">
                    <div className="h-2 w-1/3 bg-zinc-800 rounded" />
                    <div className="space-y-2">
                      <div className="h-12 w-full border border-zinc-800 rounded flex items-center px-4 justify-between">
                        <div className="w-1/2 h-2 bg-zinc-800 rounded" />
                        <div className="w-12 h-4 bg-blue-900/20 rounded" />
                      </div>
                      <div className="h-12 w-full border border-zinc-800 rounded flex items-center px-4 justify-between">
                        <div className="w-1/2 h-2 bg-zinc-800 rounded" />
                        <div className="w-12 h-4 bg-blue-900/20 rounded" />
                      </div>
                    </div>
                  </div>
                  {/* Active Highlighter */}
                  <div className="absolute top-20 left-6 right-6 h-12 border-2 border-yellow-500/50 rounded bg-yellow-500/5 flex items-center justify-center">
                    <div className="bg-black text-yellow-500 text-[10px] px-2 py-0.5 rounded-full border border-yellow-500 absolute -top-3 left-2 font-mono">
                      interaction_target
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>

        </div>

        {/* Stats Section */}
        <div className="mt-32 border-y border-white/5 bg-black/50 backdrop-blur">
          <div className="container mx-auto px-6 py-16">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="space-y-1">
                <h3 className="text-5xl font-bold text-white tracking-tight">80B+</h3>
                <p className="text-zinc-500 text-sm font-medium uppercase tracking-wider">Tokens Scraped</p>
              </div>
              <div className="space-y-1 md:border-l border-white/10 md:pl-12">
                <h3 className="text-5xl font-bold text-white tracking-tight">200K+</h3>
                <p className="text-zinc-500 text-sm font-medium uppercase tracking-wider">Browser Hours Served</p>
              </div>
              <div className="space-y-1 md:border-l border-white/10 md:pl-12">
                <h3 className="text-5xl font-bold text-white tracking-tight">&lt;1s</h3>
                <p className="text-zinc-500 text-sm font-medium uppercase tracking-wider">Avg. Session Start Time</p>
              </div>
            </div>
          </div>
        </div>

        {/* Features Bento Grid */}
        <div className="py-32 container mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-20">
            <h2 className="text-3xl md:text-5xl font-bold mb-6">Everything you need to <br /> scale your agents.</h2>
            <p className="text-zinc-400 text-lg">Built for performance, reliability, and stealth from the ground up.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-6 gap-6 max-w-6xl mx-auto">
            {/* Large Card 1 */}
            <div className="col-span-1 md:col-span-4 bg-[#0A0A0A] border border-white/10 rounded-2xl p-8 relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="w-12 h-12 bg-white/5 rounded-lg flex items-center justify-center mb-6 text-white border border-white/10">
                  <Fingerprint size={24} />
                </div>
                <h3 className="text-xl font-bold mb-3">Anti-detection Fingerprinting</h3>
                <p className="text-zinc-400 text-sm leading-relaxed max-w-sm">
                  Advanced fingerprint masking technology ensures your agents blend in with real user traffic. Bypass bot detection and captchas effortlessly.
                </p>
              </div>
              {/* Visual Decoration */}
              <div className="absolute bottom-0 right-0 w-64 h-32 bg-gradient-to-t from-blue-500/10 to-transparent blur-2xl" />
            </div>

            {/* Small Card 2 */}
            <div className="col-span-1 md:col-span-2 bg-[#0A0A0A] border border-white/10 rounded-2xl p-8 relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="w-12 h-12 bg-white/5 rounded-lg flex items-center justify-center mb-6 text-white border border-white/10">
                <Zap size={24} />
              </div>
              <h3 className="text-xl font-bold mb-3">Sub-ms Latency</h3>
              <p className="text-zinc-400 text-sm leading-relaxed">
                Optimized for speed with global edge locations.
              </p>
            </div>

            {/* Small Card 3 */}
            <div className="col-span-1 md:col-span-2 bg-[#0A0A0A] border border-white/10 rounded-2xl p-8 relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="w-12 h-12 bg-white/5 rounded-lg flex items-center justify-center mb-6 text-white border border-white/10">
                <Code2 size={24} />
              </div>
              <h3 className="text-xl font-bold mb-3">Simple API</h3>
              <p className="text-zinc-400 text-sm leading-relaxed">
                Control browsers with standard WebSocket protocols.
              </p>
            </div>

            {/* Large Card 4 */}
            <div className="col-span-1 md:col-span-4 bg-[#0A0A0A] border border-white/10 rounded-2xl p-8 relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10 flex flex-col md:flex-row gap-8 items-start md:items-center">
                <div className="flex-1">
                  <div className="w-12 h-12 bg-white/5 rounded-lg flex items-center justify-center mb-6 text-white border border-white/10">
                    <Globe size={24} />
                  </div>
                  <h3 className="text-xl font-bold mb-3">Residential Proxies</h3>
                  <p className="text-zinc-400 text-sm leading-relaxed max-w-sm">
                    Access millions of residential IP addresses to route your traffic through legitimate devices worldwide.
                  </p>
                </div>
                <div className="flex-1 w-full bg-black/50 rounded-lg border border-white/10 p-4 font-mono text-[10px] text-zinc-500">
                  <div><span className="text-purple-400">await</span> browser.connect({`{`}</div>
                  <div className="pl-4">proxy: <span className="text-green-400">"residential"</span>,</div>
                  <div className="pl-4">country: <span className="text-green-400">"US"</span></div>
                  <div>{`}`})</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 bg-[#0A0A0A] relative z-10">
        <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-white text-black rounded-sm flex items-center justify-center font-bold text-xs">
              <Terminal size={14} />
            </div>
            <span className="font-semibold text-zinc-400">Ghost Inc.</span>
          </div>
          <div className="text-xs text-zinc-600">
            © 2024 Ghost Inc. All rights reserved.
          </div>
        </div>
      </footer>

    </div>
  );
}
