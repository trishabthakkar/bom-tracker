import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/auth/useAuth";

export function PublicRoute() {
  const { loading, user } = useAuth();

  if (loading) {
    return (
      <div
        className="grid min-h-screen place-items-center bg-background text-sm text-muted-foreground"
        role="status"
        aria-live="polite"
      >
        Loading...
      </div>
    );
  }

  if (user) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
