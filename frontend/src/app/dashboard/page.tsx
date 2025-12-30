"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { supabase } from "@/lib/supabase";
import {
    Terminal, ArrowRight, Activity, Settings,
    ExternalLink, Copy, Eye, EyeOff, Search,
    LayoutGrid, Zap, History, Loader2, Skull,
    LogOut, Coffee, MonitorPlay, ChevronDown, Check,
    Plus, Clock, Inbox, Sparkles, Filter
} from "lucide-react";
import Link from "next/link";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// =============================================
// Types
// =============================================

interface Job {
    id: string;
    user_id: string;
    goal: string;
    status: string;
    current_url?: string;
    steel_session_id: string | null;
    steel_viewer_url: string | null;
    temporal_workflow_id: string | null;
    created_at: string;
}

interface TaskLog {
    id: string;
    job_id: string;
    action: string | null;
    reasoning: string | null;
    finished: boolean;
    created_at: string;
}

// =============================================
// Components
// =============================================

const StatusBadge = ({ status }: { status: string }) => {
    const colors: Record<string, string> = {
        running: "text-blue-400 bg-blue-400/10 border-blue-400/20",
        completed: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
        waiting_approval: "text-amber-400 bg-amber-400/10 border-amber-400/20",
        waiting_info: "text-purple-400 bg-purple-400/10 border-purple-400/20",
        failed: "text-red-400 bg-red-400/10 border-red-400/20",
        rejected: "text-red-400 bg-red-400/10 border-red-400/20",
        killed: "text-zinc-400 bg-zinc-400/10 border-zinc-400/20",
        pending: "text-zinc-400 bg-zinc-400/10 border-zinc-400/20",
        initializing: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    };

    return (
        <span className={cn("text-xs font-normal px-2 py-0.5 rounded-sm border", colors[status] || colors.pending)}>
            {status.replace("_", " ")}
        </span>
    );
};

const Skeleton = ({ className }: { className?: string }) => (
    <div className={cn("animate-pulse duration-1000 bg-white/[0.03] rounded-sm", className)} />
);

const Toast = ({ message, onClose }: { message: string, onClose: () => void }) => (
    <div className="fixed bottom-6 right-6 z-[100] animate-in fade-in slide-in-from-bottom-2 duration-300">
        <div className="bg-[#18181b] border border-white/10 rounded-sm px-4 py-3 shadow-2xl flex items-center gap-3">
            <div className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-500 flex items-center justify-center">
                <Check size={12} />
            </div>
            <span className="text-sm font-medium text-zinc-200">{message}</span>
        </div>
    </div>
);

// =============================================
// Main Dashboard Component
// =============================================

export default function DashboardPage() {
    const router = useRouter();
    const { user, loading: authLoading, signOut } = useAuth();

    const [activeTab, setActiveTab] = useState<"quickstart" | "sessions">("quickstart");
    const [profileOpen, setProfileOpen] = useState(false);

    // Jobs State
    const [jobs, setJobs] = useState<Job[]>([]);
    const [pastJobs, setPastJobs] = useState<Job[]>([]);
    const [activeJob, setActiveJob] = useState<Job | null>(null);
    const [taskLogs, setTaskLogs] = useState<TaskLog[]>([]);
    const [showPastJobs, setShowPastJobs] = useState(false);
    const [isLoadingJobs, setIsLoadingJobs] = useState(true);
    const [isKilling, setIsKilling] = useState(false);

    // UI State
    const [rightPanelTab, setRightPanelTab] = useState<"details" | "logs" | "agent_logs">("details");
    const [toasts, setToasts] = useState<{ id: string; message: string }[]>([]);

    const addToast = (message: string) => {
        const id = Math.random().toString(36).substring(2, 9);
        setToasts(prev => [...prev, { id, message }]);
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 3000);
    };

    const handleCopy = (text: string, label: string) => {
        navigator.clipboard.writeText(text);
        addToast(`${label} copied to clipboard`);
    };

    // Redirect if not authenticated
    useEffect(() => {
        if (!authLoading && !user) {
            router.push("/login");
        }
    }, [user, authLoading, router]);

    const fetchJobs = useCallback(async () => {
        if (!user) return;
        setIsLoadingJobs(true);

        const { data: activeData } = await supabase
            .from("jobs")
            .select("*")
            .eq("user_id", user.id)
            .in("status", ["pending", "initializing", "running", "waiting_approval", "waiting_info"])
            .order("created_at", { ascending: false })
            .limit(20);
        if (activeData) setJobs(activeData);

        const { data: pastData } = await supabase
            .from("jobs")
            .select("*")
            .eq("user_id", user.id)
            .in("status", ["completed", "failed", "rejected", "killed"])
            .order("created_at", { ascending: false })
            .limit(50);
        if (pastData) setPastJobs(pastData);

        setIsLoadingJobs(false);
    }, [user]);

    useEffect(() => {
        fetchJobs();
        if (!user) return;

        const subscription = supabase
            .channel("jobs_realtime")
            .on("postgres_changes", { event: "*", schema: "public", table: "jobs", filter: `user_id=eq.${user.id}` }, () => fetchJobs())
            .subscribe();

        return () => {
            supabase.removeChannel(subscription);
        };
    }, [user, fetchJobs]);

    useEffect(() => {
        if (!activeJob) {
            setTaskLogs([]);
            return;
        }
        const fetchLogs = async () => {
            const { data } = await supabase.from("task_logs").select("*").eq("job_id", activeJob.id).order("created_at", { ascending: true });
            if (data) setTaskLogs(data);
        };
        fetchLogs();
        const subscription = supabase.channel(`logs_${activeJob.id}`).on("postgres_changes", { event: "INSERT", schema: "public", table: "task_logs", filter: `job_id=eq.${activeJob.id}` }, (payload) => setTaskLogs(prev => [...prev, payload.new as TaskLog])).subscribe();
        return () => {
            supabase.removeChannel(subscription);
        };
    }, [activeJob?.id]);

    const getSteelViewerUrl = (job: Job) => {
        // Priority: Use the viewer URL from the job (should be debugUrl from Steel API)
        if (job.steel_viewer_url) {
            // Add interactive=false for view-only mode (no mouse/keyboard control)
            const url = new URL(job.steel_viewer_url);
            if (!url.searchParams.has('interactive')) {
                url.searchParams.set('interactive', 'false');
            }
            return url.toString();
        }
        return null;
    };

    if (authLoading || !user) return null;

    const currentJobs = showPastJobs ? pastJobs : jobs;

    const DetailRow = ({ label, value, isCode = false, copyable = false }: { label: string, value: React.ReactNode, isCode?: boolean, copyable?: boolean }) => (
        <div className="flex items-center justify-between py-3 border-b border-white/5 last:border-0 hover:bg-white/[0.02] transition-colors px-4 -mx-4 group">
            <span className="text-zinc-500 text-sm font-medium">{label}</span>
            <div className="flex items-center gap-2 max-w-[60%] justify-end">
                <span className={cn("text-zinc-300 text-sm truncate", isCode && "text-xs")}>
                    {value}
                </span>
                {copyable && typeof value === 'string' && (
                    <button
                        onClick={() => handleCopy(value, label)}
                        className="text-zinc-600 hover:text-zinc-300 transition-all opacity-0 group-hover:opacity-100 hover:scale-110 active:scale-95"
                    >
                        <Copy size={12} />
                    </button>
                )}
            </div>
        </div>
    );

    return (
        <div className="flex flex-col h-screen bg-[#050505] text-white font-sans overflow-hidden selection:bg-white/10 selection:text-white">

            {/* TOASTS */}
            {toasts.map(toast => (
                <Toast key={toast.id} message={toast.message} onClose={() => setToasts(prev => prev.filter(t => t.id !== toast.id))} />
            ))}

            {/* HEADER */}
            <header className="flex flex-col border-b border-white/5 bg-[#050505] shrink-0 sticky top-0 z-50">
                {/* Top Row: Brand & Actions */}
                <div className="h-14 flex items-center justify-between px-6">
                    <Link href="/" className="hover:text-white transition-all flex items-center gap-2 group hover:scale-[1.02] active:scale-100 mr-2">
                        <div className="w-6 h-6 bg-white/10 rounded-sm flex items-center justify-center text-white group-hover:bg-white/20 transition-all shadow-inner">
                            <Terminal size={12} />
                        </div>
                        <span className="font-bold tracking-tight text-zinc-300 group-hover:text-white transition-colors">GHOST</span>
                    </Link>

                    <div className="flex items-center gap-4">
                        <div className="hidden md:flex items-center gap-4 text-xs text-zinc-500 mr-2">
                            <a href="#" className="hover:text-zinc-300 flex items-center gap-1.5 transition-colors">Docs <ArrowRight size={10} className="-rotate-45" /></a>
                            <a href="#" className="hover:text-zinc-300 flex items-center gap-1.5 transition-colors">Discord <ArrowRight size={10} className="-rotate-45" /></a>
                        </div>
                        <button className="px-3 py-1.5 border border-white/10 rounded-sm text-xs font-medium text-zinc-400 hover:text-white hover:bg-white/5 transition-all active:scale-95">
                            Feedback
                        </button>
                        <div className="h-4 w-px bg-white/10"></div>

                        {/* Profile Dropdown */}
                        <div className="relative">
                            <button
                                onClick={() => setProfileOpen(!profileOpen)}
                                className="flex items-center justify-center group"
                            >
                                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-[10px] font-bold text-white border border-white/10 group-hover:border-white/30 transition-all shadow-[0_0_15px_rgba(37,99,235,0.2)] group-active:scale-90">
                                    {user.email?.[0].toUpperCase()}
                                </div>
                            </button>

                            {profileOpen && (
                                <>
                                    <div className="fixed inset-0 z-40" onClick={() => setProfileOpen(false)} />
                                    <div className="absolute right-0 top-full mt-2 w-56 bg-black border border-white/10 rounded-sm shadow-2xl z-50 py-1.5 animate-in fade-in duration-500 origin-top-right">
                                        <div className="px-4 py-3 border-b border-white/5 mb-1.5">
                                            <p className="text-xs text-zinc-500 font-light mb-1">Authenticated as</p>
                                            <p className="text-sm text-zinc-200 font-medium truncate">{user.email}</p>
                                        </div>
                                        <Link href="/settings" className="flex items-center gap-3 px-4 py-2 text-sm text-zinc-400 hover:bg-white/5 hover:text-white w-full text-left transition-colors">
                                            <Settings size={14} /> Settings
                                        </Link>
                                        <button onClick={signOut} className="flex items-center gap-3 px-4 py-2 text-sm text-red-400/80 hover:bg-red-500/10 hover:text-red-400 w-full text-left transition-colors">
                                            <LogOut size={14} /> Sign Out
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                {/* Bottom Row: Tabs */}
                <div className="h-10 flex items-center px-6">
                    <nav className="flex items-center h-full gap-6 text-sm font-medium">
                        <button
                            onClick={() => { setActiveTab("quickstart"); setActiveJob(null); }}
                            className={cn(
                                "h-full relative flex items-center transition-all px-0.5",
                                activeTab === "quickstart" ? "text-white" : "text-zinc-500 hover:text-zinc-300"
                            )}
                        >
                            Quickstart
                            {activeTab === "quickstart" && (
                                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-white rounded-t-full transition-all" />
                            )}
                        </button>

                        <button
                            onClick={() => { setActiveTab("sessions"); setActiveJob(null); }}
                            className={cn(
                                "h-full relative flex items-center transition-all px-0.5",
                                activeTab === "sessions" && !activeJob ? "text-white" : "text-zinc-500 hover:text-zinc-300"
                            )}
                        >
                            Sessions
                            {activeTab === "sessions" && !activeJob && (
                                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-white rounded-t-full transition-all" />
                            )}
                        </button>

                        {activeJob && activeTab === "sessions" && (
                            <div className="flex items-center h-full animate-in fade-in duration-500 ease-out">
                                <div className="h-full relative flex items-center gap-2.5 text-white font-medium px-0.5">
                                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
                                    <span className="text-sm tracking-tight capitalize">Session #{activeJob.id.substring(0, 8)}</span>
                                    <button
                                        onClick={() => handleCopy(activeJob.id, "Session ID")}
                                        className="text-zinc-600 hover:text-zinc-400 transition-colors"
                                    >
                                        <Copy size={12} />
                                    </button>
                                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-white rounded-t-full animate-in fade-in slide-in-from-bottom-1" />
                                </div>
                            </div>
                        )}
                    </nav>
                </div>
            </header>

            {/* CONTENT AREA */}
            <main key={activeTab} className="flex-1 overflow-hidden relative flex pt-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
                {activeTab === "quickstart" ? (
                    <div className="flex-1 overflow-y-auto custom-scrollbar p-8 bg-[#050505]">
                        <div className="max-w-5xl mx-auto space-y-12">
                            {/* Agent Configuration Info */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
                                {/* LEFT: Agent Info */}
                                <div className="space-y-8">
                                    <div>
                                        <h1 className="text-4xl font-light text-white mb-6 tracking-tight">Setup your agent.</h1>
                                        <p className="text-zinc-400 text-lg leading-relaxed font-light">
                                            Control your sovereign browser fleet by simply sending emails. No complex integrations required.
                                        </p>
                                    </div>

                                    <div className="bg-black border border-white/5 rounded-sm p-6 relative overflow-hidden group">
                                        <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                                            <Inbox size={32} />
                                        </div>
                                        <label className="text-xs text-zinc-500 font-light mb-4 block">Your Private Agent Email</label>
                                        <div className="flex items-center gap-3 mb-4">
                                            <code className="flex-1 bg-black/50 border border-white/10 rounded-sm px-4 py-4 text-sm text-blue-400 break-all selection:bg-blue-500/20 group-hover:border-white/20 transition-colors">
                                                ghost@reluit.com
                                            </code>
                                        </div>
                                        <button
                                            onClick={() => handleCopy("ghost@reluit.com", "Agent Email")}
                                            className="w-full flex items-center justify-center gap-2.5 px-4 py-3 bg-white text-black hover:bg-zinc-200 rounded-sm text-sm font-semibold transition-all shadow-lg active:scale-[0.98]"
                                        >
                                            <Copy size={16} /> Copy Address
                                        </button>
                                        <p className="text-[10px] text-zinc-600 mt-5 leading-relaxed font-medium">
                                            Emails sent to this address will spin up a browser session automatically.
                                        </p>
                                    </div>
                                </div>

                                {/* RIGHT: Timeline */}
                                <div className="relative border-l border-white/5 ml-4 lg:ml-0 space-y-12 py-4">

                                    {/* Step 1 */}
                                    <div className="relative pl-8">
                                        <div className="absolute -left-[5px] top-2 w-2.5 h-2.5 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                                        <h3 className="text-lg font-medium text-white mb-1.5">Compose Instruction</h3>
                                        <p className="text-zinc-500 text-sm mb-4 font-light">
                                            Send an email with your task as the subject.
                                        </p>
                                        <div className="bg-black border border-white/10 rounded-sm p-4 max-w-md shadow-2xl">
                                            <div className="text-xs text-zinc-500 font-light mb-3 pb-3 border-b border-white/5 flex justify-between">
                                                <span>To: Ghost Agent</span>
                                                <span className="opacity-40">just now</span>
                                            </div>
                                            <div className="text-zinc-200 text-sm font-medium mb-1.5">Research iPhone 15 prices</div>
                                            <div className="text-zinc-500 text-xs text-justify leading-relaxed font-normal">
                                                Check Amazon and Apple.com for the base model 128GB and report back with the best deals found...
                                            </div>
                                        </div>
                                    </div>

                                    {/* Step 2 */}
                                    <div className="relative pl-8">
                                        <div className="absolute -left-[5px] top-2 w-2.5 h-2.5 rounded-full bg-zinc-800" />
                                        <h3 className="text-lg font-medium text-white mb-1.5">Agent Reply</h3>
                                        <p className="text-zinc-500 text-sm mb-4 font-light">
                                            Your agent confirms the task has started.
                                        </p>
                                        <div className="bg-black border border-white/10 rounded-sm p-4 flex items-start gap-4 max-w-md shadow-xl">
                                            <div className="mt-0.5 w-7 h-7 rounded-sm bg-white/5 text-zinc-400 flex items-center justify-center flex-shrink-0 border border-white/10">
                                                <Terminal size={14} />
                                            </div>
                                            <div>
                                                <div className="text-xs font-light text-zinc-500 mb-1.5 flex items-center gap-2">
                                                    Ghost System
                                                </div>
                                                <p className="text-xs text-zinc-400 leading-relaxed font-normal">
                                                    "Task received. Initializing browser session. I'll report back shortly with a breakdown of pricing."
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Step 3 */}
                                    <div className="relative pl-8">
                                        <div className="absolute -left-[5px] top-2 w-2.5 h-2.5 rounded-full bg-zinc-800" />
                                        <h3 className="text-lg font-medium text-white mb-1.5">Live Monitor</h3>
                                        <p className="text-zinc-500 text-sm font-light">
                                            Go to the <button onClick={() => setActiveTab("sessions")} className="text-blue-400 hover:text-blue-300 underline underline-offset-4 decoration-blue-500/30 transition-all font-medium">Sessions</button> tab to watch your agent work in real-time.
                                        </p>
                                    </div>
                                </div>
                            </div>

                        </div>
                    </div>
                ) : (
                    <div className="flex-1 flex flex-col overflow-hidden bg-[#050505]">
                        {activeJob ? (
                            // SPECIFIC SESSION VIEW
                            <div className="flex flex-1 w-full bg-[#09090b] h-full overflow-hidden">
                                {/* LEFT COLUMN: Video/Session */}
                                <div className="flex-1 flex flex-col border-r border-white/5 relative bg-black">
                                    <div className="flex-1 flex items-center justify-center p-8 bg-[#050505] relative overflow-hidden">
                                        <div className="absolute inset-0 bg-grid-pattern-subtle opacity-20 pointer-events-none" />

                                        {/* Video Container */}
                                        <div className="w-full h-full max-h-[800px] flex flex-col bg-black border border-white/10 rounded-sm shadow-[0_20px_50px_rgba(0,0,0,0.8)] relative overflow-hidden group animate-in fade-in duration-500">
                                            {/* Fake Browser Toolbar */}
                                            <div className="h-9 bg-[#18181b] border-b border-white/5 flex items-center px-4 gap-4">
                                                <div className="flex gap-1.5">
                                                    <div className="w-3 h-3 rounded-full bg-red-500/40 border border-red-500/20"></div>
                                                    <div className="w-3 h-3 rounded-full bg-amber-500/40 border border-amber-500/20"></div>
                                                    <div className="w-3 h-3 rounded-full bg-green-500/40 border border-green-500/20"></div>
                                                </div>
                                                <div className="flex-1 bg-black rounded-sm h-6 border border-white/5 flex items-center px-3 text-[11px] text-zinc-500 group-hover:border-white/20 transition-colors">
                                                    <span className="text-blue-500/80 mr-2">🔒</span> {activeJob.current_url || "about:blank"}
                                                </div>
                                                <div className="h-full flex items-center">
                                                    <StatusBadge status={activeJob.status} />
                                                </div>
                                            </div>

                                            {activeJob.steel_session_id ? (
                                                <iframe
                                                    src={getSteelViewerUrl(activeJob) || "about:blank"}
                                                    className="w-full h-full border-none bg-white animate-in fade-in duration-1000"
                                                    allow="clipboard-read; clipboard-write; microphone; camera"
                                                />
                                            ) : (
                                                <div className="flex items-center justify-center h-full text-zinc-500 flex-col gap-4">
                                                    <Loader2 size={36} className="animate-spin text-zinc-700" />
                                                    <span className="text-xs text-zinc-500 font-light">Handshaking with session...</span>
                                                </div>
                                            )}

                                            {/* Media Controls Overlay */}
                                            <div className="absolute bottom-0 left-0 right-0 h-16 bg-black/80 flex items-end px-8 py-5 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-2 group-hover:translate-y-0 text-zinc-400">
                                                <div className="w-full flex items-center gap-6">
                                                    <button className="hover:text-white transition-all transform hover:scale-110 active:scale-95"><MonitorPlay size={22} /></button>
                                                    <span className="text-[11px] font-medium">LIVE</span>
                                                    <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden cursor-pointer group/track relative">
                                                        <div className="w-full h-full bg-zinc-700"></div>
                                                        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-zinc-400"></div>
                                                    </div>
                                                    <span className="text-[11px] font-medium">REC</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* RIGHT COLUMN: Info Side Panel */}
                                <div className="w-[420px] bg-[#0A0A0A] flex flex-col border-l border-white/5 h-full animate-in slide-in-from-right-4 duration-500">
                                    {/* Tabs */}
                                    <div className="flex items-center border-b border-white/5 px-4 bg-[#0A0A0A]">
                                        <button
                                            onClick={() => setRightPanelTab("details")}
                                            className={cn(
                                                "relative px-4 py-4 text-xs font-light transition-all",
                                                rightPanelTab === "details" ? "text-white" : "text-zinc-600 hover:text-zinc-300"
                                            )}
                                        >
                                            Metadata
                                            {rightPanelTab === "details" && <div className="absolute bottom-0 left-2 right-2 h-0.5 bg-white rounded-full"></div>}
                                        </button>
                                        <button
                                            onClick={() => setRightPanelTab("logs")}
                                            className={cn(
                                                "relative px-4 py-4 text-xs font-light transition-all",
                                                rightPanelTab === "logs" ? "text-white" : "text-zinc-600 hover:text-zinc-300"
                                            )}
                                        >
                                            Task Stream
                                            {rightPanelTab === "logs" && <div className="absolute bottom-0 left-2 right-2 h-0.5 bg-white rounded-full"></div>}
                                        </button>
                                    </div>

                                    {/* Panel Content */}
                                    <div className="flex-1 overflow-y-auto custom-scrollbar p-6 bg-[#0A0A0A]">
                                        {rightPanelTab === "details" && (
                                            <div className="space-y-1 animate-in fade-in duration-500">
                                                <div className="mb-8">
                                                    <h4 className="text-xs font-light text-zinc-500 mb-4">Core Identification</h4>
                                                    <DetailRow label="ID" value={activeJob.id} isCode copyable />
                                                    <DetailRow label="Created" value={new Date(activeJob.created_at).toLocaleString()} />
                                                </div>

                                                <div className="mb-8">
                                                    <h4 className="text-xs font-light text-zinc-500 mb-4">Environment</h4>
                                                    <DetailRow label="Display" value="1280x768 (LCD)" />
                                                    <DetailRow label="Engine" value="Chrome 136.0.0.0" isCode />
                                                    <DetailRow label="Signals" value="Selenium Hidden" />
                                                </div>

                                                <div className="mb-8">
                                                    <h4 className="text-xs font-light text-zinc-500 mb-4">Billing Metrics</h4>
                                                    <DetailRow label="Compute Unit" value="Standard v1" />
                                                    <DetailRow label="Total Cost" value="$0.0016" isCode />
                                                </div>
                                            </div>
                                        )}

                                        {rightPanelTab === "logs" && (
                                            <div className="text-xs space-y-4 animate-in fade-in duration-500">
                                                {taskLogs.length === 0 && (
                                                    <div className="flex flex-col items-center justify-center py-20 text-zinc-600 gap-3">
                                                        <div className="w-8 h-8 rounded-full border border-zinc-800 flex items-center justify-center animate-spin-slow">
                                                            <div className="w-1 h-1 rounded-full bg-zinc-600"></div>
                                                        </div>
                                                        <span className="text-[10px]">Awaiting execution trace...</span>
                                                    </div>
                                                )}
                                                {taskLogs.map((log, i) => (
                                                    <div key={log.id} className="group border-l border-white/5 pl-4 relative hover:border-blue-500/30 transition-colors">
                                                        <div className="absolute left-[-4.5px] top-1 w-2 h-2 rounded-full bg-[#050505] border border-white/10 transition-colors group-hover:bg-blue-500 group-hover:border-blue-500/50"></div>
                                                        <div className="flex items-center gap-3 mb-1.5 opacity-40 group-hover:opacity-100 transition-opacity">
                                                            <span className="text-[10px] text-zinc-500">[{new Date(log.created_at).toLocaleTimeString()}]</span>
                                                            <div className="h-px flex-1 bg-white/5"></div>
                                                        </div>
                                                        <span className={cn("text-sm transition-colors", log.action ? "text-blue-400 font-medium" : "text-zinc-400 font-light")}>
                                                            {log.action ? (
                                                                <div className="flex items-start gap-2">
                                                                    <ArrowRight size={14} className="mt-1 shrink-0" />
                                                                    <span>EXECUTING: {log.action}</span>
                                                                </div>
                                                            ) : log.reasoning}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            // LIST VIEW
                            <div className="flex-1 flex flex-col p-8 bg-[#050505] overflow-y-auto custom-scrollbar">
                                <div className="max-w-6xl mx-auto w-full space-y-10">
                                    <div className="flex items-end justify-between border-b border-white/5 pb-8">
                                        <div>
                                            <h1 className="text-3xl font-light text-white tracking-tight mb-2">Browser Sessions</h1>
                                            <p className="text-zinc-500 font-light">Monitor and manage your active browsing instances.</p>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <div className="flex h-9 bg-black border border-white/10 rounded-sm p-0.5">
                                                <button onClick={() => setShowPastJobs(false)} className={cn("px-5 h-full text-xs rounded-sm transition-all font-light", !showPastJobs ? "bg-white text-black shadow-lg" : "text-zinc-500 hover:text-zinc-300")}>Live</button>
                                                <button onClick={() => setShowPastJobs(true)} className={cn("px-5 h-full text-xs rounded-sm transition-all font-light", showPastJobs ? "bg-white text-black shadow-lg" : "text-zinc-500 hover:text-zinc-300")}>Archive</button>
                                            </div>
                                            <button
                                                onClick={fetchJobs}
                                                className="h-9 w-9 flex items-center justify-center bg-black border border-white/10 rounded hover:border-white/20 hover:bg-white/5 transition-all active:scale-95 text-zinc-400"
                                            >
                                                <History size={14} />
                                            </button>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 gap-3">
                                        {isLoadingJobs ? (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                {Array.from({ length: 4 }).map((_, i) => (
                                                    <Skeleton key={i} className="h-40 w-full" />
                                                ))}
                                            </div>
                                        ) : currentJobs.length > 0 ? (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                {currentJobs.map((job, idx) => (
                                                    <div
                                                        key={job.id}
                                                        onClick={() => setActiveJob(job)}
                                                        className="bg-[#0c0c0e] border border-white/10 rounded-sm p-6 hover:border-white/30 hover:bg-[#121214] cursor-pointer transition-all group relative overflow-hidden animate-in fade-in duration-500 fill-mode-both"
                                                        style={{ animationDelay: `${idx * 40}ms` }}
                                                    >
                                                        <div className="flex flex-col h-full justify-between gap-8">
                                                            <div className="flex justify-between items-start">
                                                                <div className="w-10 h-10 rounded-sm bg-black border border-white/10 flex items-center justify-center text-zinc-500 group-hover:text-white transition-all group-hover:scale-110">
                                                                    <CategoryIcon job={job} />
                                                                </div>
                                                                <StatusBadge status={job.status} />
                                                            </div>
                                                            <div>
                                                                <h3 className="text-lg font-normal text-white group-hover:text-blue-400 transition-colors mb-2 truncate">
                                                                    {job.goal || "Unnamed Protocol"}
                                                                </h3>
                                                                <div className="flex items-center gap-4 text-xs text-zinc-500 font-light">
                                                                    <span className="flex items-center gap-1.5"><Zap size={14} className="text-blue-500/50" /> {job.id.substring(0, 8)}</span>
                                                                    <span className="flex items-center gap-1.5"><Clock size={14} /> {new Date(job.created_at).toLocaleDateString()}</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div className="absolute right-5 bottom-5 w-9 h-9 rounded-full bg-white/5 flex items-center justify-center text-zinc-400 group-hover:bg-white group-hover:text-black transition-all transform group-hover:scale-110">
                                                            <ArrowRight size={18} />
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="text-center py-32 border border-white/5 border-dashed rounded-sm bg-[#050505] flex flex-col items-center gap-6 animate-in fade-in duration-500">
                                                <div className="w-20 h-20 rounded-full bg-[#0A0A0A] border border-white/5 flex items-center justify-center text-zinc-800">
                                                    <Inbox size={32} />
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-white font-normal text-lg">Clear session history.</p>
                                                    <p className="text-zinc-600 text-sm font-light">No {showPastJobs ? "archived" : "active"} sessions were found on this node.</p>
                                                </div>
                                                <button onClick={() => setActiveTab("quickstart")} className="px-6 py-2.5 bg-white text-black text-xs font-bold rounded-sm hover:bg-zinc-200 transition-colors active:scale-95 mt-4">Initialize Agent</button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}

function CategoryIcon({ job }: { job: Job }) {
    const goal = job.goal?.toLowerCase() || "";
    if (goal.includes('research') || goal.includes('find') || goal.includes('search')) return <Search size={20} />;
    if (goal.includes('monitor') || goal.includes('watch') || goal.includes('track')) return <Activity size={20} />;
    if (goal.includes('buy') || goal.includes('shop') || goal.includes('order')) return <Zap size={20} />;
    return <Terminal size={20} />;
}
