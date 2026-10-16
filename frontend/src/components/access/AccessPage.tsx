"use client";

import { useState, type FormEvent } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { demoAccountKey, roleHome, teacherApplicationKey, type DemoAccount, type TeacherApplication } from "@/data/demoAccount";
import { initialProfile } from "@/data/profile";
import { setDemoRole } from "@/lib/demoSessionClient";
import { writeDemoStorage } from "@/lib/useDemoStorage";
import styles from "./AccessPage.module.css";

type Mode = "login" | "register" | "recover" | "teacher";

const copy: Record<Mode, { title: string; description: string; action: string }> = {
  login: { title: "Entrar", description: "Conecte-se a professores, cursos e aulas para estudar para o vestibular.", action: "Entrar na demonstração" },
  register: { title: "Criar conta de aluno", description: "Comece a organizar seus estudos na AprovaAí.", action: "Criar conta de demonstração" },
  recover: { title: "Recuperar acesso", description: "Informe seu e-mail para simular a recuperação de acesso.", action: "Solicitar recuperação" },
  teacher: { title: "Cadastro de professor", description: "Solicite a análise do seu cadastro para publicar cursos.", action: "Enviar solicitação" },
};

export function AccessPage({ mode }: { mode: Mode }) {
  const router = useRouter();
  const [notice, setNotice] = useState("");
  const [role, setRole] = useState<DemoAccount["role"]>("student");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const email = String(data.get("email") ?? "").trim();
    if (mode === "recover") {
      setNotice(`Solicitação simulada para ${email}. Nenhum e-mail foi enviado.`);
      return;
    }

    const name = String(data.get("name") ?? "").trim() || "Estudante";
    if (mode === "teacher") {
      const application: TeacherApplication = { name, email, area: String(data.get("area") ?? "").trim(), status: "pending" };
      writeDemoStorage(teacherApplicationKey, application);
      router.push("/professor/solicitacao");
      return;
    }

    const accountRole = mode === "register" ? "student" : role;
    const demoName = accountRole === "student" ? initialProfile.nickname : accountRole === "teacher" ? "Prof. Fulano" : "Administração";
    const account: DemoAccount = { name: mode === "register" ? name : demoName, email, role: accountRole };
    writeDemoStorage(demoAccountKey, account);
    setDemoRole(account.role);
    router.replace(roleHome[account.role]);
    router.refresh();
  }

  return (
    <main className={styles.page}>
      <section className={styles.card} aria-labelledby="access-title">
        <Link className={styles.logo} href="/" aria-label="AprovaAí, voltar ao início"><Image src="/aprova-ai-logo.svg" alt="AprovaAí" width={280} height={70} priority /></Link>
        <h1 id="access-title">{copy[mode].title}</h1>
        <p className={styles.description}>{copy[mode].description}</p>
        <form className={styles.form} onSubmit={submit}>
          {(mode === "register" || mode === "teacher") && <label>Nome completo<input autoComplete="name" name="name" required /></label>}
          <label>E-mail<span className={styles.inputWithIcon}><Image src="/login-mail.svg" alt="" width={18} height={18} /><input autoComplete="email" name="email" placeholder="nome@exemplo.com" required type="email" /></span></label>
          {mode === "login" && <label>Senha<span className={styles.inputWithIcon}><Image src="/login-lock.svg" alt="" width={18} height={18} /><input autoComplete="current-password" name="password" required type="password" /></span></label>}
          {mode === "login" && <label>Entrar como<select value={role} onChange={(event) => setRole(event.target.value as DemoAccount["role"])}><option value="student">Aluno</option><option value="teacher">Professor</option><option value="admin">Administrador</option></select></label>}
          {mode === "teacher" && <label>Área de ensino<input name="area" placeholder="Ex.: Física" required /></label>}
          <button className={styles.primaryButton} type="submit">{copy[mode].action}</button>
        </form>
        {notice && <p className={styles.notice} role="status">{notice}</p>}
        <div className={styles.links}>
          {mode === "login" ? <><Link href="/recuperar-acesso">Esqueceu sua senha?</Link><Link href="/cadastro">Criar conta</Link></> : <Link href="/login">Voltar para entrar</Link>}
          {mode === "register" && <Link href="/cadastro/professor">Sou professor</Link>}
        </div>
        <p className={styles.demoNote}>Protótipo: nenhum acesso é autenticado e nenhuma senha é armazenada.</p>
      </section>
    </main>
  );
}
