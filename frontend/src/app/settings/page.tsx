"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Save, User, Shield, Bell, Key } from "lucide-react";
import { useAuth } from "@/lib/auth";

export default function SettingsPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState("general");

    return (
        <div className="min-h-screen bg-[#050505] text-white font-sans">

            {/* Header */}
            <header className="h-16 border-b border-white/5 bg-[#050505] flex items-center px-6 sticky top-0 z-50">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard" className="p-2 -ml-2 text-zinc-500 hover:text-white hover:bg-white/5 rounded-sm transition-colors">
                        <ArrowLeft size={18} />
                    </Link>
                    <div className="h-4 w-px bg-white/10"></div>
                    <h1 className="font-medium text-sm">Workspace Settings</h1>
                </div>
            </header>

            <main className="max-w-screen-xl mx-auto px-6 py-12 flex flex-col lg:flex-row gap-12">

                {/* Sidebar Nav */}
                <aside className="w-full lg:w-64 flex-shrink-0 space-y-1">
                    <button
                        onClick={() => setActiveTab("general")}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-sm text-sm font-medium transition-colors ${activeTab === "general" ? "bg-white/10 text-white" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"}`}
                    >
                        <User size={16} /> General
                    </button>
                    <button
                        onClick={() => setActiveTab("security")}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-sm text-sm font-medium transition-colors ${activeTab === "security" ? "bg-white/10 text-white" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"}`}
                    >
                        <Shield size={16} /> Security
                    </button>
                    <button
                        onClick={() => setActiveTab("api")}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-sm text-sm font-medium transition-colors ${activeTab === "api" ? "bg-white/10 text-white" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"}`}
                    >
                        <Key size={16} /> API Keys
                    </button>
                    <button
                        onClick={() => setActiveTab("notifications")}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-sm text-sm font-medium transition-colors ${activeTab === "notifications" ? "bg-white/10 text-white" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"}`}
                    >
                        <Bell size={16} /> Notifications
                    </button>
                </aside>

                {/* Content */}
                <div className="flex-1 max-w-2xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">

                    {activeTab === "general" && (
                        <div className="space-y-8">
                            <div>
                                <h2 className="text-xl font-light text-white mb-1">General Information</h2>
                                <p className="text-sm text-zinc-500">Manage your workspace identity and preferences.</p>
                            </div>

                            <div className="space-y-6 border border-white/5 bg-zinc-900/20 p-6 rounded-sm">
                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-zinc-400 uppercase tracking-wider">Workspace Name</label>
                                    <input type="text" defaultValue="My Workspace" className="w-full bg-black border border-white/10 rounded-sm px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50" />
                                </div>

                                <div className="space-y-2">
                                    <label className="text-xs font-mono text-zinc-400 uppercase tracking-wider">Owner Email</label>
                                    <input type="email" defaultValue={user?.email || ""} disabled className="w-full bg-zinc-900 border border-white/5 rounded-sm px-3 py-2 text-sm text-zinc-500 cursor-not-allowed" />
                                    <p className="text-[10px] text-zinc-600">Contact support to change your email address.</p>
                                </div>
                            </div>

                            <div className="flex justify-end">
                                <button className="flex items-center gap-2 px-4 py-2 bg-white text-black hover:bg-zinc-200 rounded-sm text-sm font-medium transition-colors">
                                    <Save size={16} /> Save Changes
                                </button>
                            </div>
                        </div>
                    )}

                    {activeTab === "security" && (
                        <div className="space-y-8">
                            <div>
                                <h2 className="text-xl font-light text-white mb-1">Security</h2>
                                <p className="text-sm text-zinc-500">Manage your password and authentication methods.</p>
                            </div>
                            <div className="p-6 border border-yellow-500/10 bg-yellow-500/5 rounded-sm">
                                <p className="text-sm text-yellow-500 mb-2 font-medium">Password Reset</p>
                                <p className="text-zinc-400 text-xs mb-4">You can request a password reset email to update your credentials.</p>
                                <button className="px-3 py-1.5 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-500 border border-yellow-500/20 rounded-sm text-xs transition-colors">
                                    Send Reset Link
                                </button>
                            </div>
                        </div>
                    )}

                    {activeTab === "api" && (
                        <div className="space-y-8">
                            <div>
                                <h2 className="text-xl font-light text-white mb-1">API Keys</h2>
                                <p className="text-sm text-zinc-500">Manage programmatic access to your workspace.</p>
                            </div>
                            <div className="border border-white/5 bg-zinc-900/20 p-6 rounded-sm text-center">
                                <Key size={24} className="mx-auto text-zinc-600 mb-2" />
                                <p className="text-sm text-zinc-400 mb-4">You haven't generated any API keys yet.</p>
                                <button className="px-4 py-2 bg-white text-black hover:bg-zinc-200 rounded-sm text-sm font-medium transition-colors">
                                    Generate New Key
                                </button>
                            </div>
                        </div>
                    )}

                </div>
            </main>
        </div>
    );
}
