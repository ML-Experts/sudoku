import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { AuthTokenApiResponse } from "../types/api";

type AdminMode = "demo" | "admin";

type AdminSessionContextValue = {
  mode: AdminMode;
  authToken: AuthTokenApiResponse | null;
  loginModalOpen: boolean;
  loginPromptMessage: string | null;
  continueInDemoMode: () => void;
  openLoginModal: () => void;
  applyAdminSession: (token: AuthTokenApiResponse) => void;
  clearAdminSessionAndRequireLogin: (message: string) => void;
  logoutAdmin: () => void;
};

const STORAGE_KEY = "sudokuAdminAuthToken";

const AdminSessionContext = createContext<AdminSessionContextValue | null>(null);

function isFutureDate(timestamp: string): boolean {
  const milliseconds = Date.parse(timestamp);
  if (Number.isNaN(milliseconds)) {
    return false;
  }

  return milliseconds > Date.now();
}

function loadStoredToken(): AuthTokenApiResponse | null {
  const raw = window.sessionStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as AuthTokenApiResponse;
    if (
      typeof parsed.accessToken !== "string" ||
      typeof parsed.tokenType !== "string" ||
      typeof parsed.expiresAtUtc !== "string"
    ) {
      return null;
    }

    if (!isFutureDate(parsed.expiresAtUtc)) {
      return null;
    }

    return parsed;
  } catch {
    return null;
  }
}

function saveStoredToken(token: AuthTokenApiResponse): void {
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(token));
}

function clearStoredToken(): void {
  window.sessionStorage.removeItem(STORAGE_KEY);
}

export function AdminSessionProvider({ children }: { children: ReactNode }) {
  const [authToken, setAuthToken] = useState<AuthTokenApiResponse | null>(() =>
    loadStoredToken()
  );
  const [loginModalOpen, setLoginModalOpen] = useState<boolean>(
    () => loadStoredToken() === null
  );
  const [loginPromptMessage, setLoginPromptMessage] = useState<string | null>(null);

  const mode: AdminMode = authToken ? "admin" : "demo";

  const continueInDemoMode = useCallback(() => {
    setLoginModalOpen(false);
    setLoginPromptMessage(null);
  }, []);

  const openLoginModal = useCallback(() => {
    setLoginModalOpen(true);
  }, []);

  const applyAdminSession = useCallback((token: AuthTokenApiResponse) => {
    saveStoredToken(token);
    setAuthToken(token);
    setLoginModalOpen(false);
    setLoginPromptMessage(null);
  }, []);

  const clearAdminSessionAndRequireLogin = useCallback((message: string) => {
    clearStoredToken();
    setAuthToken(null);
    setLoginPromptMessage(message);
    setLoginModalOpen(true);
  }, []);

  const logoutAdmin = useCallback(() => {
    clearAdminSessionAndRequireLogin(
      "Zostales wylogowany z trybu administracyjnego."
    );
  }, [clearAdminSessionAndRequireLogin]);

  useEffect(() => {
    if (!authToken) {
      return;
    }

    const expirationMs = Date.parse(authToken.expiresAtUtc);
    if (Number.isNaN(expirationMs) || expirationMs <= Date.now()) {
      clearAdminSessionAndRequireLogin(
        "Sesja administracyjna wygasla. Zaloguj sie ponownie."
      );
      return;
    }

    const timeoutId = window.setTimeout(() => {
      clearAdminSessionAndRequireLogin(
        "Sesja administracyjna wygasla. Zaloguj sie ponownie."
      );
    }, expirationMs - Date.now());

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [authToken, clearAdminSessionAndRequireLogin]);

  const value = useMemo<AdminSessionContextValue>(
    () => ({
      mode,
      authToken,
      loginModalOpen,
      loginPromptMessage,
      continueInDemoMode,
      openLoginModal,
      applyAdminSession,
      clearAdminSessionAndRequireLogin,
      logoutAdmin,
    }),
    [
      mode,
      authToken,
      loginModalOpen,
      loginPromptMessage,
      continueInDemoMode,
      openLoginModal,
      applyAdminSession,
      clearAdminSessionAndRequireLogin,
      logoutAdmin,
    ]
  );

  return (
    <AdminSessionContext.Provider value={value}>
      {children}
    </AdminSessionContext.Provider>
  );
}

export function useAdminSession(): AdminSessionContextValue {
  const context = useContext(AdminSessionContext);
  if (!context) {
    throw new Error("useAdminSession must be used within AdminSessionProvider.");
  }

  return context;
}
