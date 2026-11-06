"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  demoAccountKey,
  demoRoleCookieName,
  parseDemoRole,
  type DemoAccount,
} from "@/data/demoAccount";
import { ApiError, getCurrentUserFromApi, isApiConfigured } from "@/lib/apiClient";
import { clearDemoRole, setDemoRole } from "@/lib/demoSessionClient";
import { writeDemoStorage } from "@/lib/useDemoStorage";

function currentRoleFromCookie() {
  const cookie = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${demoRoleCookieName}=`));
  return parseDemoRole(cookie?.slice(demoRoleCookieName.length + 1));
}

export function ApiSessionSync() {
  const router = useRouter();
  const [validationError, setValidationError] = useState("");

  useEffect(() => {
    const previousRole = currentRoleFromCookie();
    if (!isApiConfigured || !previousRole) return;

    let active = true;
    getCurrentUserFromApi()
      .then((user) => {
        if (!active) return;
        const account: DemoAccount = {
          name: user.email.split("@")[0] || user.email,
          email: user.email,
          role: user.role,
        };
        writeDemoStorage(demoAccountKey, account);
        setDemoRole(user.role);
        if (previousRole !== user.role) router.refresh();
      })
      .catch((error: unknown) => {
        if (!active) return;
        if (error instanceof ApiError && error.status === 401) {
          clearDemoRole();
          router.replace("/login");
          router.refresh();
          return;
        }

        const detail = error instanceof Error ? ` ${error.message}` : "";
        setValidationError(
          `Não foi possível validar a sessão com a API.${detail}`,
        );
      });

    return () => {
      active = false;
    };
  }, [router]);

  return validationError ? <p role="alert">{validationError}</p> : null;
}
