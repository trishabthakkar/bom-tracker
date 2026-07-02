import { Factory } from "lucide-react";
import { Outlet } from "react-router-dom";

export function AuthLayout() {
  return (
    <main className="grid min-h-screen bg-background px-4 py-8 text-foreground lg:grid-cols-[0.9fr_1.1fr] lg:p-0">
      <section className="hidden border-r bg-card lg:flex lg:flex-col lg:justify-between lg:p-10">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Factory className="h-5 w-5" />
          </span>
          <div>
            <p className="text-sm font-semibold">BOM Tracker</p>
            <p className="text-xs text-muted-foreground">Engineering intelligence layer</p>
          </div>
        </div>
        <div className="max-w-md space-y-4">
          <p className="text-sm font-medium text-muted-foreground">Secure workspace</p>
          <h1 className="text-3xl font-semibold tracking-normal">
            Analyze engineering change impact with confidence.
          </h1>
          <p className="text-sm leading-6 text-muted-foreground">
            Authentication is required before accessing BOM, ECO, report, graph,
            history, or settings workspaces.
          </p>
        </div>
        <p className="text-xs text-muted-foreground">
          AI-Assisted BOM Change Intelligence Layer
        </p>
      </section>

      <section className="flex items-center justify-center">
        <Outlet />
      </section>
    </main>
  );
}
