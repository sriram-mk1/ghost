"use client";

import Link from "next/link";
import {
  ArrowRight,
  ChevronRight,
  Command,
  Globe,
  LayoutGrid,
  Shield,
  Zap
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#050505] text-white font-sans overflow-x-hidden selection:bg-orange-500/30">

      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#050505]/80 backdrop-blur-xl border-b border-white/5 h-16 transition-all duration-300">
        <div className="container mx-auto px-6 h-full flex items-center justify-between">
          <div className="flex items-center gap-12">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 group">
              <div className="relative w-6 h-6 flex items-center justify-center">
                {/* Stylized 'V' logo */}
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-white">
                  <path d="M12 22L3 4H7L12 14L17 4H21L12 22Z" fill="currentColor" />
                </svg>
              </div>
              <span className="font-semibold text-lg tracking-tight ml-1">Vertex</span>
            </Link>

            {/* Main Nav Links */}
            <div className="hidden md:flex items-center gap-6 text-[13px] font-medium text-zinc-400">
              {["Product", "Solutions", "Resources", "Enterprise", "Customers", "Pricing"].map((item) => (
                <Link key={item} href="#" className="hover:text-white transition-colors">
                  {item}
                </Link>
              ))}
            </div>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-[13px] font-medium text-zinc-400 hover:text-white transition-colors">
              Sign In
            </Link>
            <Link
              href="/signup"
              className="text-[13px] font-medium bg-white text-black hover:bg-zinc-200 px-4 py-2 rounded-[4px] transition-colors"
            >
              Login
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="pt-32 pb-20 relative z-10">

        {/* Hero Content */}
        <section className="container mx-auto px-6 flex flex-col items-center text-center mb-20">

          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[11px] font-medium text-zinc-400 mb-8 hover:bg-white/10 transition-colors cursor-pointer">
            <span className="text-orange-500 font-bold tracking-widest text-[9px] uppercase">New</span>
            <span className="w-px h-3 bg-white/10 mx-1"></span>
            <span>Introducing Vertex AI 2.0</span>
            <ArrowRight size={12} className="ml-1" />
          </div>

          <h1 className="text-5xl sm:text-7xl font-medium tracking-tighter leading-[1.05] text-white max-w-4xl mx-auto mb-8">
            Bridge the gap between <br />
            <span className="text-zinc-400">clicks and capital</span>
          </h1>

          <p className="text-lg text-zinc-500 leading-relaxed max-w-xl mx-auto font-normal mb-10">
            The developer-first engine for attribution, partner performance, and deep conversion intelligence.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/start"
              className="px-6 py-3 bg-[#1A1A1A] hover:bg-[#252525] text-white text-[13px] font-medium rounded-[4px] border border-white/10 transition-all flex items-center gap-2 group"
            >
              Get Started
              <ChevronRight size={14} className="text-zinc-500 group-hover:text-white transition-colors" />
            </Link>
            <Link
              href="/contact"
              className="px-6 py-3 bg-transparent hover:bg-white/5 text-zinc-300 text-[13px] font-medium rounded-[4px] border border-white/10 transition-all"
            >
              Book a strategy call
            </Link>
          </div>
        </section>

        {/* Dashboard Preview */}
        <section className="container mx-auto px-2 sm:px-6 relative">

          {/* Dot Matrix Background Pattern (Orange/Red) */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] -z-10 opacity-30 select-none pointer-events-none"
            style={{
              backgroundImage: 'radial-gradient(#F97316 1px, transparent 1px)',
              backgroundSize: '24px 24px',
              maskImage: 'radial-gradient(ellipse at center, black 40%, transparent 70%)'
            }}>
          </div>

          <div className="relative rounded-xl border border-white/10 bg-[#0A0A0A] shadow-2xl overflow-hidden max-w-5xl mx-auto">
            {/* Window Controls */}
            <div className="bg-[#0A0A0A] border-b border-white/5 px-4 py-3 flex items-center justify-between">
              <div className="flex gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-zinc-800" />
                <div className="w-2.5 h-2.5 rounded-full bg-zinc-800" />
                <div className="w-2.5 h-2.5 rounded-full bg-zinc-800" />
              </div>
              <div className="text-[10px] items-center flex gap-2 text-zinc-600 font-mono bg-[#111] px-2 py-1 rounded border border-white/5">
                <Shield size={10} />
                secure://vertex.dashboard
              </div>
              <div className="w-8"></div> {/* Spacer */}
            </div>

            {/* Dashboard Content */}
            <div className="p-8 bg-[#0A0A0A]">
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h3 className="text-xl font-medium text-white mb-1">Your Links</h3>
                  <p className="text-sm text-zinc-500">Manage, analyze, and optimize your partner links in real-time.</p>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1.5 text-xs font-medium text-zinc-400 bg-white/5 border border-white/10 rounded hover:text-white hover:bg-white/10 transition-colors">
                    Filter Data
                  </button>
                  <button className="px-3 py-1.5 text-xs font-medium text-white bg-orange-600/10 border border-orange-500/20 text-orange-500 rounded hover:bg-orange-600/20 transition-colors flex items-center gap-1.5">
                    <span className="text-lg leading-none mb-0.5">+</span> Create Link
                  </button>
                </div>
              </div>

              {/* Stats Cards Row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                {[
                  { label: "Total Clicks", value: "2,420", change: "+12%" },
                  { label: "Conversions", value: "843", change: "+5%" },
                  { label: "Revenue", value: "$64,200", change: "+24%" },
                  { label: "Conversion Rate", value: "4.8%", change: "-1%" }
                ].map((stat) => (
                  <div key={stat.label} className="bg-[#111] border border-white/5 p-4 rounded-lg">
                    <div className="text-[11px] text-zinc-500 font-medium uppercase tracking-wider mb-2">{stat.label}</div>
                    <div className="flex items-end justify-between">
                      <div className="text-2xl font-medium text-white tracking-tight">{stat.value}</div>
                      <div className={`text-xs font-medium ${stat.change.startsWith('+') ? 'text-green-500' : 'text-red-500'}`}>
                        {stat.change}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Table / List */}
              <div className="border border-white/5 rounded-lg overflow-hidden">
                <div className="bg-[#111]/50 px-4 py-3 border-b border-white/5 grid grid-cols-12 gap-4 text-[11px] font-medium text-zinc-500 uppercase tracking-wider">
                  <div className="col-span-4">Active Links</div>
                  <div className="col-span-2 text-right hidden md:block">Events</div>
                  <div className="col-span-2 text-right hidden md:block">Conv.</div>
                  <div className="col-span-2 text-right hidden md:block">Value</div>
                  <div className="col-span-8 md:col-span-2 text-right">Status</div>
                </div>

                {[
                  { name: "vertex-link", domain: "v.inc/partner-alpha", events: "124k", conv: "3.2k", value: "$12.4k", status: "Active" },
                  { name: "gradient.com", domain: "v.inc/gradient-flow", events: "98k", conv: "2.8k", value: "$9.1k", status: "Active" },
                  { name: "assisi-client.com", domain: "v.inc/assisi-summer", events: "45k", conv: "1.1k", value: "$3.5k", status: "Active" },
                  { name: "hyper-scale.io", domain: "v.inc/hyper-q4", events: "12k", conv: "240", value: "$980", status: "Paused" },
                ].map((row, i) => (
                  <div key={i} className="bg-[#0A0A0A] px-4 py-3 border-b border-white/5 grid grid-cols-12 gap-4 items-center group hover:bg-white/[0.02] transition-colors last:border-0">
                    <div className="col-span-4 flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-gradient-to-br from-zinc-800 to-zinc-900 border border-white/10 flex items-center justify-center text-white/40">
                        <Command size={14} />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-white">{row.name}</div>
                        <div className="text-[11px] text-zinc-600 font-mono hidden sm:block">{row.domain}</div>
                      </div>
                    </div>
                    <div className="col-span-2 text-right text-xs text-zinc-400 tabular-nums hidden md:block">{row.events}</div>
                    <div className="col-span-2 text-right text-xs text-zinc-400 tabular-nums hidden md:block">{row.conv}</div>
                    <div className="col-span-2 text-right text-xs text-white font-medium tabular-nums hidden md:block">{row.value}</div>
                    <div className="col-span-8 md:col-span-2 text-right flex justify-end">
                      <div className={`px-2 py-0.5 rounded-full text-[10px] font-medium inline-flex items-center gap-1.5 
                        ${row.status === 'Active' ? 'bg-green-500/10 text-green-500 border border-green-500/20' : 'bg-zinc-800 text-zinc-400 border border-zinc-700'}`}>
                        {row.status === 'Active' && <div className="w-1 h-1 rounded-full bg-green-500 animate-pulse" />}
                        {row.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Trusted By */}
        <section className="py-20 border-b border-white/5">
          <div className="container mx-auto px-6 text-center">
            <p className="text-zinc-500 text-sm mb-10">Trusted by 1k companies and developers</p>
            <div className="flex flex-wrap justify-center items-center gap-12 md:gap-20 opacity-40 grayscale mix-blend-screen">
              <h4 className="text-xl font-bold tracking-tight text-white">OpenAI</h4>
              <h4 className="text-xl font-bold tracking-tight text-white">Linear</h4>
              <h4 className="text-xl font-bold tracking-tight text-white">DATADOG</h4>
              <h4 className="text-xl font-bold tracking-tight text-white">RIPPLING</h4>
              <h4 className="text-xl font-bold tracking-tight text-white">Figma</h4>
              <h4 className="text-xl font-bold tracking-tight text-white">ramp</h4>
            </div>
          </div>
        </section>

        {/* Features / Foundation */}
        <section className="py-32 container mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-20 items-center">
            <div className="max-w-xl">
              <p className="text-orange-500 text-xs font-bold tracking-widest uppercase mb-4">Core Technology</p>
              <h2 className="text-4xl md:text-5xl font-medium text-white mb-6 tracking-tight">
                The foundation <br />
                of <span className="text-zinc-500">every journey</span>
              </h2>
              <p className="text-lg text-zinc-400 mb-8 leading-relaxed">
                Deploy white-label reclamation nodes with industrial-grade logic, dynamic handoffs, geo-targeting, and deep link resolution.
              </p>
              <div className="flex items-center gap-4">
                <button className="px-6 py-3 bg-white text-black font-medium text-sm rounded-[4px] hover:bg-zinc-200 transition-colors">
                  Browse Edge Features
                </button>
                <button className="px-6 py-3 bg-transparent border border-white/10 text-white font-medium text-sm rounded-[4px] hover:bg-white/5 transition-colors">
                  Learn More
                </button>
              </div>
            </div>

            {/* Feature Visualization (List) */}
            <div className="relative">
              {/* Dot Pattern again for consistency */}
              <div className="absolute inset-0 z-0 opacity-20 pointer-events-none"
                style={{
                  backgroundImage: 'radial-gradient(#F97316 1px, transparent 1px)',
                  backgroundSize: '24px 24px',
                  maskImage: 'radial-gradient(circle at center, black 0%, transparent 80%)'
                }}
              />

              <div className="relative z-10 space-y-4">
                {[
                  { icon: <Zap size={16} />, label: "vertex-link", tag: "ROOT", time: "12ms", status: "Active" },
                  { icon: <Globe size={16} />, label: "gradient.com", tag: "NODE", time: "45ms", status: "Active" },
                  { icon: <LayoutGrid size={16} />, label: "assisi-client.com", tag: "EDGE", time: "28ms", status: "Active" },
                ].map((item, i) => (
                  <div key={i} className="bg-[#0A0A0A] border border-white/10 p-4 rounded-lg flex items-center justify-between shadow-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-zinc-900 rounded flex items-center justify-center text-white border border-white/5">
                        {item.icon}
                      </div>
                      <div>
                        <div className="text-sm font-medium text-white flex items-center gap-2">
                          {item.label}
                          {item.tag && <span className="text-[9px] bg-red-500/20 text-red-500 px-1.5 py-0.5 rounded border border-red-500/20">{item.tag}</span>}
                        </div>
                        <div className="text-xs text-zinc-500 font-mono mt-0.5">v.inc/secure-route-{i + 10}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <span className="text-xs text-zinc-500 font-mono">{item.time}</span>
                      <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-green-500/10 border border-green-500/20 text-[10px] text-green-500 font-medium uppercase tracking-wide">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                        {item.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 bg-[#050505]">
        <div className="container mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <h5 className="text-white font-bold mb-4">Product</h5>
            <ul className="space-y-2 text-sm text-zinc-500">
              <li><Link href="#" className="hover:text-white transition-colors">Features</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Integrations</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Pricing</Link></li>
            </ul>
          </div>
          <div>
            <h5 className="text-white font-bold mb-4">Resources</h5>
            <ul className="space-y-2 text-sm text-zinc-500">
              <li><Link href="#" className="hover:text-white transition-colors">Documentation</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">API Reference</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Status</Link></li>
            </ul>
          </div>
          <div>
            <h5 className="text-white font-bold mb-4">Company</h5>
            <ul className="space-y-2 text-sm text-zinc-500">
              <li><Link href="#" className="hover:text-white transition-colors">About</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Blog</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Careers</Link></li>
            </ul>
          </div>
          <div>
            <h5 className="text-white font-bold mb-4">Legal</h5>
            <ul className="space-y-2 text-sm text-zinc-500">
              <li><Link href="#" className="hover:text-white transition-colors">Privacy</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Terms</Link></li>
            </ul>
          </div>
        </div>
      </footer>

    </div>
  );
}
