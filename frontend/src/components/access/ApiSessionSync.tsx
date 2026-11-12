"use client";

import { useEffect, useState, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  demoAccountKey,
  demoRoleCookieName,
  parseDemoRole,
  roleHome,
  type DemoAccount,
} from "@/data/demoAccount";
import { ApiError, getCurrentUserFromApi, isApiConfigured, renewApiSession, subscribeSessionChanges } from "@/lib/apiClient";
import { requiredRoles } from "@/lib/pageAccess";
import { clearDemoRole, setDemoRole } from "@/lib/demoSessionClient";
import { writeDemoStorage } from "@/lib/useDemoStorage";

function currentRoleFromCookie() {
  const cookie = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${demoRoleCookieName}=`));
  return parseDemoRole(cookie?.slice(demoRoleCookieName.length + 1));
}

export function ApiSessionSync({children}: {children: ReactNode}) {
  const router = useRouter();
  const pathname = usePathname();
  const [result, setResult] = useState<{path: string; valid: boolean; error?: string} | null>(null);
  const [retry, setRetry] = useState(0);
  const [renewalNotice, setRenewalNotice] = useState("");
  const expected = requiredRoles(pathname);

  useEffect(() => {
    if (!isApiConfigured) return;
    const unsubscribe = subscribeSessionChanges(type => {
      if (type === "logout") {
        clearDemoRole();
        try { localStorage.removeItem(demoAccountKey); } catch { /* No persistent UI cache. */ }
        window.location.replace("/login");
      } else {
        window.location.reload();
      }
    });
    const expired = () => setRenewalNotice("Sua sessão expirou. Renove antes de repetir a operação.");
    window.addEventListener("aprovaai-session-expired", expired);
    return () => { unsubscribe(); window.removeEventListener("aprovaai-session-expired", expired); };
  }, []);

  useEffect(() => {
    const previousRole = currentRoleFromCookie();
    if (!isApiConfigured) return;

    let active = true;
    getCurrentUserFromApi(Boolean(expected || previousRole))
      .then((user) => {
        if (!active) return;
        const account: DemoAccount = {
          name: user.email.split("@")[0] || user.email,
          email: user.email,
          role: user.role,
        };
        writeDemoStorage(demoAccountKey, account);
        setDemoRole(user.role);
        if (expected && !expected.includes(user.role)) {
          router.replace(roleHome[user.role]);
          return;
        }
        setResult({path: pathname, valid: true});
        if (previousRole !== user.role) router.refresh();
      })
      .catch((error: unknown) => {
        if (!active) return;
        if (error instanceof ApiError && error.status === 401) {
          clearDemoRole();
          setResult({path: pathname, valid: false});
          if (expected) router.replace("/login");
          if (previousRole) router.refresh();
          return;
        }

        const detail = error instanceof Error ? ` ${error.message}` : "";
        setResult({path: pathname, valid: false, error: `Não foi possível validar a sessão com a API.${detail}`});
      });

    return () => {
      active = false;
    };
  }, [router, pathname, expected, retry]);

  async function renew() {
    try { await renewApiSession(); setRenewalNotice(""); setRetry(value => value + 1); }
    catch (error) { setRenewalNotice((error as Error).message); }
  }

  if (!isApiConfigured) return children;
  const current = result?.path === pathname ? result : null;
  return <>
    {current?.error && <p role="alert">{current.error} <button type="button" onClick={() => setRetry(value => value + 1)}>Tentar validar novamente</button></p>}
    {renewalNotice && <p role="alert">{renewalNotice} <button type="button" onClick={() => void renew()}>Renovar sessão</button></p>}
    {expected && !current?.valid ? <p role="status">Validando sessão...</p> : children}
  </>;
}
