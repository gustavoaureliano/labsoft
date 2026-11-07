"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { verifyEmail } from "@/lib/apiClient";

const emailFlowsEnabled = process.env.NEXT_PUBLIC_EMAIL_FLOWS_ENABLED === "true";
const verificationRequests = new Map<
  string,
  ReturnType<typeof verifyEmail>
>();

function verifyEmailOnce(token: string) {
  let request = verificationRequests.get(token);
  if (!request) {
    request = verifyEmail(token);
    verificationRequests.set(token, request);
  }
  return request;
}

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [message, setMessage] = useState("Confirmando seu e-mail...");
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!token || !emailFlowsEnabled) return;

    let cancelled = false;
    verifyEmailOnce(token)
      .then((result) => {
        if (!cancelled) setMessage(result.message);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setMessage(
            error instanceof Error
              ? error.message
              : "Não foi possível confirmar o e-mail.",
          );
          setFailed(true);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  if (!emailFlowsEnabled) {
    return <main style={{ maxWidth: 560, margin: "4rem auto", padding: "0 1.5rem" }}>
      <h1>Confirmação de e-mail indisponível</h1>
      <p>Contas novas podem entrar sem confirmar o endereço nesta versão.</p>
    </main>;
  }

  return (
    <main style={{ maxWidth: 560, margin: "4rem auto", padding: "0 1.5rem" }}>
      <meta name="referrer" content="no-referrer" />
      <h1>Confirmação de e-mail</h1>
      <p aria-live="polite" role={failed || !token ? "alert" : "status"}>
        {token ? message : "O link de confirmação está incompleto."}
      </p>
    </main>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<main>Carregando...</main>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
