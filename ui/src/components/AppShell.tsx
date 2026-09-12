import { Activity, Circle } from "lucide-react"
import type { ReactNode } from "react"

interface AppShellProps {
  children: ReactNode
}

function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border/60">
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

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Circle className="size-2 fill-current text-emerald-500" />
            <span>Agent online</span>
          </div>
        </div>
      </header>

      <main>{children}</main>
    </div>
  )
}

export default AppShell