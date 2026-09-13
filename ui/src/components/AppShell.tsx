import { Activity } from "lucide-react"
import type { ReactNode } from "react"

interface AppShellProps {
  children: ReactNode
}

function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-50 border-b border-border/60 bg-gradient-to-b from-[#fafafa]/95 to-[#f2f2f0]/95 shadow-[0_1px_8px_rgba(0,0,0,0.04)] backdrop-blur-[10px]">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex size-8 items-center justify-center rounded-lg bg-foreground text-background">
              <Activity className="size-4" strokeWidth={2.5} />
            </div>

            <div>
              <div className="text-sm font-semibold tracking-tight">
                SCÉANCE
              </div>
              <div className="text-xs text-muted-foreground">
                Always watching. Ready to recover.
              </div>
            </div>
          </div>

          <div 
            className="flex items-center gap-1.5"
            aria-label="SCÉANCE monitoring active"
            title="SCÉANCE monitoring active"
            >
            <span className="size-1.5 rounded-full bg-emerald-500 motion-safe:animate-[heartbeat_1.8s_ease-in-out_infinite]" />
            <span className="size-1.5 rounded-full bg-emerald-500/70 motion-safe:animate-[heartbeat_1.8s_ease-in-out_infinite_0.3s]" />
            <span className="size-1.5 rounded-full bg-emerald-500/40 motion-safe:animate-[heartbeat_1.8s_ease-in-out_infinite_0.6s]" />
          </div>
        </div>
      </header>

      <main>{children}</main>
    </div>
  )
}

export default AppShell