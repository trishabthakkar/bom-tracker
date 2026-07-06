import { NavLink } from "react-router-dom";
import { ChevronLeft, ChevronRight, Factory } from "lucide-react";
import { Button } from "@/components/ui/button";
import { navItems } from "@/components/layout/navItems";
import { cn } from "@/lib/utils";

type SidebarProps = {
  collapsed: boolean;
  mobileOpen: boolean;
  onToggleCollapse: () => void;
  onCloseMobile: () => void;
};

export function Sidebar({
  collapsed,
  mobileOpen,
  onToggleCollapse,
  onCloseMobile,
}: SidebarProps) {
  return (
    <>
      <button
        type="button"
        aria-label="Close sidebar"
        className={cn(
          "fixed inset-0 z-30 bg-foreground/30 backdrop-blur-sm transition-opacity lg:hidden",
          mobileOpen ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={onCloseMobile}
      />

      <aside
        aria-label="Primary navigation"
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex border-r bg-card transition-all duration-200 lg:translate-x-0",
          collapsed ? "lg:w-20" : "lg:w-72",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
          "w-72",
        )}
      >
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex h-16 items-center justify-between gap-3 border-b px-4">
            <NavLink
              to="/"
              className="flex min-w-0 items-center gap-3"
              onClick={onCloseMobile}
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <Factory className="h-5 w-5" />
              </span>
              <span className={cn("min-w-0", collapsed && "lg:hidden")}>
                <span className="block truncate text-sm font-semibold">BOM Tracker</span>
                <span className="block truncate text-xs text-muted-foreground">
                  Engineering intelligence
                </span>
              </span>
            </NavLink>

            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="hidden lg:inline-flex"
              onClick={onToggleCollapse}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {collapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </Button>
          </div>

          <nav className="flex-1 space-y-1 overflow-y-auto p-3" aria-label="Main menu">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  cn(
                    "flex h-11 items-center gap-3 rounded-md px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                    isActive && "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground",
                    collapsed && "lg:justify-center lg:px-0",
                  )
                }
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                <span className={cn("truncate", collapsed && "lg:hidden")}>
                  {item.label}
                </span>
              </NavLink>
            ))}
          </nav>
        </div>
      </aside>
    </>
  );
}
