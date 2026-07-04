"use client";

import { LogOut, UserCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { AuthSession } from "@/lib/types";
import { loginWithGoogle } from "@/lib/api";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential?: string }) => void;
          }) => void;
          renderButton: (
            element: HTMLElement,
            options: {
              theme?: "outline" | "filled_blue" | "filled_black";
              size?: "large" | "medium" | "small";
              shape?: "rectangular" | "pill" | "circle" | "square";
              text?: "signin_with" | "signup_with" | "continue_with" | "signin";
              width?: number;
            }
          ) => void;
        };
      };
    };
  }
}

type Props = {
  session: AuthSession | null;
  onLogin: (session: AuthSession) => void;
  onLogout: () => void;
};

const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

export function GoogleLoginButton({ session, onLogin, onLogout }: Props) {
  const buttonRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (session || !googleClientId || !buttonRef.current) {
      return;
    }

    const clientId = googleClientId;
    let isMounted = true;

    function renderButton() {
      if (!isMounted || !window.google || !buttonRef.current) {
        return;
      }
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response) => {
          if (!response.credential) {
            setError("Google 인증 정보를 받지 못했습니다.");
            return;
          }
          try {
            const nextSession = await loginWithGoogle(response.credential);
            onLogin(nextSession);
            setError("");
          } catch (caught) {
            setError(caught instanceof Error ? caught.message : "Google 로그인에 실패했습니다.");
          }
        }
      });
      window.google.accounts.id.renderButton(buttonRef.current, {
        theme: "outline",
        size: "large",
        shape: "rectangular",
        text: "continue_with",
        width: 260
      });
    }

    if (window.google) {
      renderButton();
    } else {
      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.onload = renderButton;
      script.onerror = () => setError("Google 로그인 스크립트를 불러오지 못했습니다.");
      document.head.appendChild(script);
    }

    return () => {
      isMounted = false;
    };
  }, [onLogin, session]);

  if (session) {
    return (
      <div className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-3">
          {session.user.picture ? (
            <img src={session.user.picture} alt="" className="h-10 w-10 rounded-full" />
          ) : (
            <UserCircle className="h-10 w-10 text-mint" aria-hidden />
          )}
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-bold text-ink">{session.user.name || "Google 계정"}</p>
            <p className="truncate text-xs text-stone-500">{session.user.email}</p>
          </div>
          <button
            type="button"
            onClick={onLogout}
            className="inline-flex h-9 items-center gap-2 rounded-md border border-stone-300 bg-white px-3 text-sm font-semibold text-stone-700 hover:bg-stone-50"
          >
            <LogOut className="h-4 w-4" aria-hidden />
            로그아웃
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
      <p className="mb-3 text-sm font-bold text-ink">계정별 기록 저장</p>
      {googleClientId ? (
        <div ref={buttonRef} />
      ) : (
        <div className="grid gap-2">
          <button
            type="button"
            disabled
            className="inline-flex h-11 w-full cursor-not-allowed items-center justify-center gap-2 rounded-md border border-stone-300 bg-stone-100 px-4 text-sm font-bold text-stone-500"
          >
            Google 로그인 설정 필요
          </button>
          <p className="text-xs leading-5 text-stone-500">
            `NEXT_PUBLIC_GOOGLE_CLIENT_ID`와 백엔드 `GOOGLE_CLIENT_ID`를 설정하면 Google 로그인 버튼이 표시됩니다.
          </p>
        </div>
      )}
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
