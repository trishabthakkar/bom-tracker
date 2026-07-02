import { useCallback, useEffect, useMemo, useState } from "react";
import { AuthContext } from "@/auth/authContext";
import {
  getCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
  type User,
} from "@/lib/authApi";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    getCurrentUser()
      .then((currentUser) => {
        if (active) {
          setUser(currentUser);
        }
      })
      .catch(() => {
        if (active) {
          setUser(null);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await loginUser({ email, password });
    setUser(response.user);
  }, []);

  const register = useCallback(
    async (payload: { email: string; password: string; full_name?: string }) => {
      const response = await registerUser(payload);
      setUser(response.user);
    },
    [],
  );

  const logout = useCallback(async () => {
    await logoutUser().catch(() => undefined);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [loading, login, logout, register, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
