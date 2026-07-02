import { Bell, Menu, Moon, Settings, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";

type NavbarProps = {
  darkMode: boolean;
  onToggleDarkMode: () => void;
  onOpenSidebar: () => void;
};

export function Navbar({
  darkMode,
  onToggleDarkMode,
  onOpenSidebar,
}: NavbarProps) {
  return (
    <header className="sticky top-0 z-20 border-b bg-card/95 backdrop-blur">
      <div className="flex h-16 items-center justify-between gap-4 px-4 lg:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={onOpenSidebar}
            aria-label="Open sidebar"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">AI-Assisted BOM Change Intelligence</p>
            <p className="hidden truncate text-xs text-muted-foreground sm:block">
              Engineering change impact workspace
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button type="button" variant="ghost" size="icon" aria-label="Notifications">
            <Bell className="h-5 w-5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onToggleDarkMode}
            aria-label="Toggle dark mode"
          >
            {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </Button>
          <Button type="button" variant="ghost" size="icon" aria-label="Settings">
            <Settings className="h-5 w-5" />
          </Button>
          <button
            type="button"
            className="flex h-9 w-9 items-center justify-center rounded-full border bg-secondary text-sm font-semibold text-secondary-foreground"
            aria-label="User menu"
          >
            TB
          </button>
        </div>
      </div>
    </header>
  );
}
