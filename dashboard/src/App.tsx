import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  BrowserRouter,
  NavLink,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";
import { Activity } from "lucide-react";
import { TooltipProvider } from "./components/ui/tooltip";
import { ScopeGateBanner } from "./components/ScopeGateBanner";
import { useLiveData, useFindingsSocket } from "./hooks/useLiveData";
import { useAegisStore } from "./store/useAegisStore";
import Dashboard from "./pages/Dashboard";
import RunExploit from "./pages/RunExploit";
import Findings from "./pages/Findings";
import Verification from "./pages/Verification";
import Evaluation from "./pages/Evaluation";
import Settings from "./pages/Settings";
import { cn } from "./lib/utils";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5_000,
      retry: 1,
    },
  },
});

const NAV = [
  { to: "/", label: "Dashboard" },
  { to: "/run", label: "Run Exploit" },
  { to: "/findings", label: "Findings" },
  { to: "/verification", label: "Verification" },
  { to: "/evaluation", label: "Evaluation" },
  { to: "/settings", label: "Settings" },
];

function Shell() {
  useLiveData();
  useFindingsSocket();
  const scope = useAegisStore((s) => s.scope);

  return (
    <div className="flex min-h-full flex-col bg-background">
      <ScopeGateBanner scope={scope} />
      <header className="flex items-center gap-6 border-b border-border bg-surface px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Activity className="size-4 text-cyan" />
          <span className="font-mono text-sm font-bold tracking-[0.2em]">
            AEGIS
          </span>
          <span className="hidden font-mono text-[10px] text-muted-foreground md:inline">
            Autonomous Exploitation-Graded Incident-Verification System
          </span>
        </div>
        <nav className="ml-2 flex items-center gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-elevated text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 lg:px-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/run" element={<RunExploit />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/verification" element={<Verification />} />
          <Route path="/evaluation" element={<Evaluation />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <BrowserRouter>
          <Shell />
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
}