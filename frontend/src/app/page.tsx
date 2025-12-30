"use client";

import Link from "next/link";
import Image from "next/image";
import {
  Terminal,
  ArrowRight,
  Play,
  Mail,
  Globe,
  Zap,
  Shield,
  Cpu,
  Layers,
  Activity
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#09090b] text-white font-sans selection:bg-blue-500/30 overflow-x-hidden">

      {/* Global Border Wrapper for Vertical Lines */}
      <div className="max-w-[1400px] mx-auto border-x border-white/5 min-h-screen relative shadow-[0_0_100px_rgba(0,0,0,0.5)] bg-[#09090b]">

        {/* Background Grid Pattern for texture */}
        <div className="absolute inset-0 z-0 pointer-events-none opacity-[0.03]"
          style={{ backgroundImage: 'url("/grid-pixel.png")', backgroundSize: '100px 100px' }}>
        </div>

        {/* Fixed Navbar */}
        <nav className="fixed top-0 left-0 right-0 z-50 bg-[#09090b]/90 backdrop-blur-md border-b border-white/5">
          <div className="max-w-[1400px] mx-auto flex h-16 items-center justify-between px-6 md:px-8 border-x border-transparent">
            {/* Inner container matches the max-w of the global wrapper essentially, but we need to account for the border lines. 
                Actually, to make lines connect perfectly, we align this inside. 
            */}
            <div className="flex items-center gap-12">
              <Link href="/" className="flex items-center gap-2 group">
                <div className="w-6 h-6 bg-white rounded-[1px] flex items-center justify-center text-black">
                  <Terminal size={14} strokeWidth={2} />
                </div>
              </Link>
              <div className="hidden md:flex items-center gap-8 text-[13px] font-light text-zinc-400">
                <Link href="#" className="hover:text-white transition-colors">Platform</Link>
                <Link href="#" className="hover:text-white transition-colors">Solutions</Link>
                <Link href="#" className="hover:text-white transition-colors">Pricing</Link>
                <Link href="#" className="hover:text-white transition-colors">Docs</Link>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <Link href="/login" className="text-[13px] font-light text-zinc-400 hover:text-white transition-colors">
                Log in
              </Link>
              <Link
                href="/signup"
                className="text-[13px] font-light bg-white text-black hover:bg-zinc-200 px-4 py-1.5 rounded-[1px] transition-colors"
              >
                Sign Up
              </Link>
            </div>
          </div>
        </nav>

        {/* Main Content Padding for Fixed Navbar */}
        <main className="pt-16">

          {/* Hero Section */}
          <section className="relative border-b border-white/5 py-32 md:py-40 px-6 md:px-8">
            <div className="max-w-4xl mx-auto text-center mb-20 relative z-10">
              <h1 className="text-5xl md:text-7xl font-light tracking-tight leading-[1.1] mb-8 text-white">
                Browser Infrastructure <br />
                <span className="text-zinc-500">for AI Agents</span>
              </h1>
              <p className="text-lg text-zinc-400 leading-relaxed font-light mb-10 max-w-xl mx-auto">
                A collaborative digital assistant that lives in the cloud. Delegate complex web tasks via email and watch it work in real-time.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  href="/signup"
                  className="w-full sm:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white text-[13px] font-light rounded-[1px] transition-colors flex items-center justify-center gap-2"
                >
                  Start For Free
                </Link>
                <Link
                  href="/demo"
                  className="w-full sm:w-auto px-8 py-3 bg-[#111] border border-white/10 hover:border-white/20 text-white text-[13px] font-light rounded-[1px] transition-colors flex items-center justify-center gap-2"
                >
                  <div className="w-4 h-4 rounded-full bg-white flex items-center justify-center">
                    <Play size={8} className="fill-black text-black ml-0.5" />
                  </div>
                  View Demo
                </Link>
              </div>
            </div>

            {/* Large Hero Placeholder Visual (Clean) */}
            <div className="max-w-6xl mx-auto relative z-10">
              <div className="aspect-video w-full bg-[#050505] border border-white/10 rounded-[1px] flex items-center justify-center relative overflow-hidden group">
                {/* Clean Placeholder - No internal grid */}

                {/* Placeholder Text/Icon */}
                <div className="text-center">
                  <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4 border border-white/5 animate-pulse">
                    <Play size={32} className="text-white/20 fill-white/5" />
                  </div>
                  <p className="text-zinc-600 font-light text-sm tracking-widest uppercase">Product Demo / Visual</p>
                </div>

                {/* Corner Accents */}
                <div className="absolute top-0 left-0 w-4 h-4 border-t border-l border-white/20"></div>
                <div className="absolute top-0 right-0 w-4 h-4 border-t border-r border-white/20"></div>
                <div className="absolute bottom-0 left-0 w-4 h-4 border-b border-l border-white/20"></div>
                <div className="absolute bottom-0 right-0 w-4 h-4 border-b border-r border-white/20"></div>
              </div>
            </div>
          </section>

          {/* Main Features Bento Grid */}
          <section className="bg-[#09090b] border-b border-white/5">
            <div className="grid lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-white/5">

              {/* Col 1 */}
              <div className="p-12 md:p-16 flex flex-col justify-between h-[500px]">
                <div className="mb-12">
                  <div className="w-10 h-10 bg-blue-500/10 rounded-[1px] flex items-center justify-center text-blue-500 mb-6">
                    <Zap size={20} strokeWidth={1.5} />
                  </div>
                  <h3 className="text-xl font-light text-white mb-3">Instant Scalability</h3>
                  <p className="text-sm font-light text-zinc-500 leading-relaxed">
                    Spin up thousands of browser sessions in seconds. No infrastructure to manage, just API calls.
                  </p>
                </div>
                <div className="h-full bg-[#050505] border border-white/5 rounded-[1px] relative overflow-hidden">
                  {/* Abstract viz */}
                  <div className="absolute bottom-0 left-0 right-0 h-full flex items-end justify-around px-4 pb-2">
                    {[40, 70, 50, 90, 60, 80].map((h, i) => (
                      <div key={i} className="w-2 bg-blue-500/20" style={{ height: `${h}%` }}></div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Col 2 (Middle Section) */}
              <div className="p-12 md:p-16 lg:col-span-1 bg-[#0b0b0d] h-[500px] flex flex-col justify-between">
                <div className="mb-12">
                  <div className="w-10 h-10 bg-white/5 rounded-[1px] flex items-center justify-center text-zinc-300 mb-6">
                    <Activity size={20} strokeWidth={1.5} />
                  </div>
                  <h3 className="text-xl font-light text-white mb-3">Live Observability</h3>
                  <p className="text-sm font-light text-zinc-500 leading-relaxed">
                    Watch your agents work in real-time with live video streaming and detailed DOM logs.
                  </p>
                </div>
                <div className="space-y-px bg-white/5 border border-white/5 rounded-[1px] overflow-hidden flex-1 flex flex-col">
                  <div className="bg-[#050505] p-3 flex items-center justify-between shrink-0">
                    <span className="text-[10px] text-zinc-500 font-mono">session_id_8fj92</span>
                    <span className="text-[10px] text-green-500 font-mono">Active</span>
                  </div>
                  <div className="bg-[#050505] p-3 flex-1 flex items-center justify-center relative">
                    {/* Faint grid bg inside stream */}
                    <div className="absolute inset-0 opacity-[0.05] bg-[url('/grid-pixel.png')] bg-[length:20px_20px]"></div>
                    <div className="text-[10px] text-zinc-700 font-mono relative z-10">Stream Placeholder</div>
                  </div>
                </div>
              </div>

              {/* Col 3 */}
              <div className="p-12 md:p-16 flex flex-col justify-between h-[500px]">
                <div className="mb-12">
                  <div className="w-10 h-10 bg-purple-500/10 rounded-[1px] flex items-center justify-center text-purple-500 mb-6">
                    <Shield size={20} strokeWidth={1.5} />
                  </div>
                  <h3 className="text-xl font-light text-white mb-3">Residential Proxy Mesh</h3>
                  <p className="text-sm font-light text-zinc-500 leading-relaxed">
                    Route traffic through millions of IP addresses to remain undetected and avoid blocks.
                  </p>
                </div>
                <div className="flex items-center gap-2 mt-4">
                  {['US', 'UK', 'DE', 'JP', 'BR'].map(c => (
                    <div key={c} className="text-[10px] text-zinc-600 border border-white/5 px-2 py-1 rounded-[1px] hover:border-white/10 cursor-default transition-colors">{c}</div>
                  ))}
                </div>
              </div>

            </div>
          </section>

          {/* Capabilities Grid (Re-introduced) */}
          <section className="py-32 px-6 md:px-8 border-b border-white/5">
            <div className="mb-20 max-w-2xl">
              <p className="text-blue-500 text-xs font-medium uppercase tracking-widest mb-4">Capabilities</p>
              <h2 className="text-3xl md:text-4xl font-light text-white mb-6">
                What you can build with Ghost
              </h2>
              <p className="text-zinc-400 text-lg font-light leading-relaxed">
                From simple data extraction to fully autonomous web agents, Ghost provides the primitives to build any browser-based workflow.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-px bg-white/5 border border-white/5 rounded-[1px] overflow-hidden">

              {/* Card 1 */}
              <div className="bg-[#0b0b0d] p-10 hover:bg-[#111] transition-colors group h-full">
                <div className="w-10 h-10 bg-blue-500/10 rounded-[1px] flex items-center justify-center text-blue-500 mb-6">
                  <Mail size={20} strokeWidth={1.5} />
                </div>
                <h3 className="text-lg font-light text-white mb-3 group-hover:text-blue-400 transition-colors">Email Agents</h3>
                <p className="text-sm font-light text-zinc-500 leading-relaxed">
                  Process invoices, categorize support tickets, and draft replies directly from your inbox.
                </p>
              </div>

              {/* Card 2 */}
              <div className="bg-[#0b0b0d] p-10 hover:bg-[#111] transition-colors group h-full">
                <div className="w-10 h-10 bg-orange-500/10 rounded-[1px] flex items-center justify-center text-orange-500 mb-6">
                  <Globe size={20} strokeWidth={1.5} />
                </div>
                <h3 className="text-lg font-light text-white mb-3 group-hover:text-orange-400 transition-colors">Web Navigation</h3>
                <p className="text-sm font-light text-zinc-500 leading-relaxed">
                  Autonomously browse complex SPAs, handle authentication, and interact with dynamic UI elements.
                </p>
              </div>

              {/* Card 3 */}
              <div className="bg-[#0b0b0d] p-10 hover:bg-[#111] transition-colors group h-full">
                <div className="w-10 h-10 bg-purple-500/10 rounded-[1px] flex items-center justify-center text-purple-500 mb-6">
                  <Zap size={20} strokeWidth={1.5} />
                </div>
                <h3 className="text-lg font-light text-white mb-3 group-hover:text-purple-400 transition-colors">Research Assistants</h3>
                <p className="text-sm font-light text-zinc-500 leading-relaxed">
                  Gather market data, compare prices, and summarize findings into structured reports.
                </p>
              </div>

              {/* Card 4 */}
              <div className="bg-[#0b0b0d] p-10 hover:bg-[#111] transition-colors group h-full">
                <div className="w-10 h-10 bg-green-500/10 rounded-[1px] flex items-center justify-center text-green-500 mb-6">
                  <Shield size={20} strokeWidth={1.5} />
                </div>
                <h3 className="text-lg font-light text-white mb-3 group-hover:text-green-400 transition-colors">Secure Delegation</h3>
                <p className="text-sm font-light text-zinc-500 leading-relaxed">
                  Enterprise-grade security with isolated browser contexts and encrypted memory management.
                </p>
              </div>
            </div>
          </section>

          {/* Additional Features List */}
          <section className="bg-[#09090b]">
            <div className="grid lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-white/5 border-b border-white/5">

              {/* Wide Feature 1 */}
              <div className="p-16 flex flex-col justify-center">
                <h3 className="text-2xl font-light text-white mb-4">Email-to-Agent Delegation</h3>
                <p className="text-sm font-light text-zinc-500 leading-relaxed mb-6 max-w-md">
                  Simply forward an email to your Ghost agent to trigger complex workflows. It understands context, attachments, and urgency.
                </p>
                <div className="inline-flex items-center gap-2 text-blue-500 text-xs font-light hover:underline cursor-pointer group">
                  Learn about AgentMail <ArrowRight size={12} className="group-hover:translate-x-0.5 transition-transform" />
                </div>
              </div>

              {/* Wide Feature 2 */}
              <div className="p-16 flex flex-col justify-center">
                <h3 className="text-2xl font-light text-white mb-4">Headless Browser API</h3>
                <p className="text-sm font-light text-zinc-500 leading-relaxed mb-8 max-w-md">
                  Full control over Chrome instances via WebSocket or REST API. Compatible with Puppeteer, Playwright, and Selenium.
                </p>
                <div className="bg-[#050505] border border-white/5 rounded-[1px] p-6 font-mono text-[11px] text-zinc-400 w-full max-w-sm">
                  <div className="flex gap-2 border-b border-white/5 pb-2 mb-2">
                    <span className="text-purple-400">POST</span>
                    <span>/v1/sessions</span>
                  </div>
                  <div className="space-y-1">
                    <div><span className="text-blue-400">"proxy"</span>: <span className="text-green-400">"residential"</span>,</div>
                    <div><span className="text-blue-400">"block_ads"</span>: <span className="text-yellow-400">true</span>,</div>
                    <div><span className="text-blue-400">"captcha_solving"</span>: <span className="text-yellow-400">true</span></div>
                  </div>
                </div>
              </div>

            </div>
          </section>


          {/* CTA Section with Glassmorphism & Ascii Background */}
          <section className="relative h-[600px] border-b border-white/5 overflow-hidden flex items-center justify-center group">

            {/* Background Image: High Quality, No Stretch */}
            <div className="absolute inset-0 z-0 bg-[#09090b]">
              <Image
                src="/beach-sunset-ascii.png"
                alt="Background"
                fill
                priority={true}
                quality={100}
                className="object-cover opacity-60 mix-blend-luminosity brightness-50"
                style={{
                  filter: 'grayscale(100%) sepia(100%) hue-rotate(190deg) saturate(200%) contrast(1.1)'
                }}
              />
              <div className="absolute inset-0 bg-blue-900/10 mix-blend-overlay"></div>
            </div>

            {/* Glassmorphic Card */}
            <div className="relative z-10 bg-black/40 backdrop-blur-2xl border border-white/10 p-16 md:p-20 text-center max-w-3xl mx-4 rounded-[1px] shadow-2xl">
              <h2 className="text-4xl md:text-5xl font-light text-white mb-6">
                Ready to hire your Ghost?
              </h2>
              <p className="text-zinc-300 font-light text-lg mb-12">
                Join the thousands of developers automating the web with our infrastructure.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
                <Link href="/signup" className="w-full sm:w-auto px-10 py-4 bg-blue-600 hover:bg-blue-500 text-white text-[13px] font-medium tracking-wide rounded-[1px] transition-colors shadow-lg">
                  Start Building
                </Link>
                <Link href="/contact" className="w-full sm:w-auto px-10 py-4 bg-transparent border border-white/20 hover:bg-white/5 text-white text-[13px] font-medium tracking-wide rounded-[1px] transition-colors">
                  Contact Sales
                </Link>
              </div>
            </div>

          </section>

          {/* Footer */}
          <footer className="bg-[#09090b] py-20 px-6 md:px-8 border-t border-white/5">
            <div className="flex flex-col md:flex-row justify-between items-start gap-12">
              <div className="space-y-6 max-w-xs">
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 bg-white rounded-[1px] flex items-center justify-center text-black">
                    <Terminal size={12} strokeWidth={2} />
                  </div>
                  <span className="font-medium text-white text-sm">Ghost</span>
                </div>
                <p className="text-xs text-zinc-500 font-light leading-relaxed">
                  Browser infrastructure for the AI era.
                </p>
              </div>

              <div className="flex gap-20 text-xs text-zinc-500 font-light">
                <div className="space-y-4">
                  <h4 className="text-white font-medium">Product</h4>
                  <ul className="space-y-2">
                    <li className="hover:text-white cursor-pointer transition-colors">API</li>
                    <li className="hover:text-white cursor-pointer transition-colors">Pricing</li>
                    <li className="hover:text-white cursor-pointer transition-colors">Enterprise</li>
                  </ul>
                </div>
                <div className="space-y-4">
                  <h4 className="text-white font-medium">Resources</h4>
                  <ul className="space-y-2">
                    <li className="hover:text-white cursor-pointer transition-colors">Documentation</li>
                    <li className="hover:text-white cursor-pointer transition-colors">Guides</li>
                    <li className="hover:text-white cursor-pointer transition-colors">Status</li>
                  </ul>
                </div>
                <div className="space-y-4">
                  <h4 className="text-white font-medium">Company</h4>
                  <ul className="space-y-2">
                    <li className="hover:text-white cursor-pointer transition-colors">Blog</li>
                    <li className="hover:text-white cursor-pointer transition-colors">Careers</li>
                    <li className="hover:text-white cursor-pointer transition-colors">Twitter</li>
                  </ul>
                </div>
              </div>
            </div>
          </footer>

        </main>

      </div>
    </div>
  );
}
