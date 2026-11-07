'use client';

import { startTransition, useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import Link from "next/link";
import { Avatar } from "./Avatar";
import { Icon } from "./Icons";
import { initialProfile, type Profile } from "../../data/profile";
import { formatPrice } from "../../data/catalog";
import { useAccess } from "@/lib/api/commerce";
import { getCurrentUserFromApi, isApiConfigured, request } from "@/lib/apiClient";
import styles from "./page.module.css";

const storageKey = "aprovaai-profile-demo";
type ApiProfile = {display_name: string; preferences: Record<string, string | number | boolean | null>; avatar_url: string | null};

export function ProfilePage() {
  const [form, setForm] = useState<Profile>(isApiConfigured ? {nickname:"",email:"",description:""} : initialProfile);
  const [savedName, setSavedName] = useState(isApiConfigured ? "Carregando perfil" : initialProfile.nickname);
  const [avatar, setAvatar] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const [access, , accessReady, accessError] = useAccess();
  const fileInput = useRef<HTMLInputElement>(null);
  const [preferences, setPreferences] = useState<ApiProfile["preferences"]>({});
  const currentPlan = access.subscription;

  useEffect(() => {
    if (isApiConfigured) {
      let active = true;
      Promise.all([getCurrentUserFromApi(), request<ApiProfile>("/api/v1/profiles/me")]).then(([user, profile]) => {
        if (!active) return;
        startTransition(() => {
          setForm({nickname: profile.display_name, email: user.email,
            description: typeof profile.preferences.description === "string" ? profile.preferences.description : ""});
          setPreferences(profile.preferences);
          setSavedName(profile.display_name);
        });
      }).catch(error => { if (active) setNotice(`Não foi possível carregar o perfil: ${(error as Error).message}`); });
      return () => { active = false; };
    }
    try {
      const saved = window.localStorage.getItem(storageKey);
      if (saved) {
        const parsed: unknown = JSON.parse(saved);
        if (parsed && typeof parsed === "object" && "nickname" in parsed && "email" in parsed && "description" in parsed) {
          const p = parsed as Profile;
          if (typeof p.nickname === "string" && typeof p.email === "string" && typeof p.description === "string") {
            startTransition(() => {
              setForm(p);
              setSavedName(p.nickname);
            });
          }
        }
      }
    } catch { /* A demo remains usable if local storage is unavailable. */ }
  }, []);

  useEffect(() => {
    if (!notice) return;
    const timeout = window.setTimeout(() => setNotice(""), 4500);
    return () => window.clearTimeout(timeout);
  }, [notice]);

  useEffect(() => () => { if (avatar) URL.revokeObjectURL(avatar); }, [avatar]);

  const update = (field: keyof Profile) => (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
  };

  const save = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isApiConfigured) {
      try {
        const saved = await request<ApiProfile>("/api/v1/profiles/me", {method:"PATCH",
          body: JSON.stringify({display_name:form.nickname, preferences:{...preferences, description:form.description}})});
        setSavedName(saved.display_name);
        setPreferences(saved.preferences);
        setNotice("Perfil salvo na plataforma.");
      } catch (error) { setNotice(`Não foi possível salvar o perfil: ${(error as Error).message}`); }
      return;
    }
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(form));
      setSavedName(form.nickname);
      setNotice("Modificações salvas neste navegador.");
    } catch {
      setNotice("Não foi possível salvar os dados neste navegador.");
    }
  };

  const chooseAvatar = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) { setNotice("Escolha um arquivo de imagem."); return; }
    if (file.size > 5 * 1024 * 1024) { setNotice("A imagem deve ter até 5 MB."); return; }
    setAvatar(URL.createObjectURL(file));
    setNotice("Avatar atualizado para esta sessão.");
  };

  return (
    <div className={styles.profile}>
      <header className={styles.pageHeading}>
        <div>
          <span className={styles.eyebrow}>Sua conta</span>
          <h1>Seu perfil</h1>
          <p>Gerencie seus dados pessoais e sua assinatura.</p>
        </div>
      </header>

      <div className={styles.topGrid}>
        <section className={`${styles.card} ${styles.avatarCard}`} aria-labelledby="avatar-title">
          <div className={styles.avatarVisual}>
            <button type="button" className={styles.avatarButton} disabled={isApiConfigured} onClick={() => fileInput.current?.click()} aria-label="Alterar avatar">
              <Avatar size="large" image={avatar} />
            </button>
          </div>
          <div className={styles.avatarInfo}>
            <span className={styles.eyebrow}>Foto do perfil</span>
            <h2 id="avatar-title">{savedName}</h2>
            <p>Estudante</p>
            {isApiConfigured ? <p>Alteração de foto ainda não disponível.</p> : <button type="button" className={styles.secondaryButton} onClick={() => fileInput.current?.click()}>Alterar foto</button>}
          </div>
          <input ref={fileInput} type="file" accept="image/*" className={styles.visuallyHidden} onChange={chooseAvatar} aria-label="Selecionar imagem do avatar" />
        </section>

        <section className={`${styles.card} ${styles.personalCard}`} aria-labelledby="personal-title">
          <div className={styles.sectionHeading}>
            <div>
              <span className={styles.eyebrow}>Informações da conta</span>
              <h2 id="personal-title">Dados pessoais</h2>
            </div>
          </div>
          <form method="post" onSubmit={event => void save(event)} className={styles.form}>
            <label htmlFor="nickname">Apelido</label>
            <input id="nickname" name="nickname" value={form.nickname} onChange={update("nickname")} required maxLength={60} />

            <label htmlFor="email">Email</label>
            <input id="email" name="email" type="email" value={form.email} onChange={update("email")} readOnly={isApiConfigured} required />

            <label htmlFor="password">Senha</label>
            <div className={styles.passwordRow}>
              <input id="password" value="••••••••••••••" type="text" readOnly aria-label="Senha oculta" />
              <button type="button" className={styles.secondaryButton} onClick={() => setNotice("A alteração de senha precisa ser conectada à API de autenticação.")}>Mudar senha</button>
            </div>

            <label htmlFor="description" className={styles.descriptionLabel}>Descrição</label>
            <textarea id="description" name="description" rows={3} value={form.description} onChange={update("description")} maxLength={500} />

            <div className={styles.formActions}><button className={styles.primaryButton} type="submit">Salvar modificações</button></div>
          </form>
        </section>
      </div>

      <div className={styles.bottomGrid}>
        {isApiConfigured ? <section className={`${styles.card} ${styles.planCard}`}>
          <h2>Acessos da conta</h2>
          {accessError ? <p role="alert">{accessError}</p> : !accessReady ? <p>Consultando acessos...</p>
            : <p>{access.courseIds.length} {access.courseIds.length === 1 ? "curso disponível" : "cursos disponíveis"}.</p>}
          <Link className={styles.secondaryButton} href="/meus-cursos">Ver meus cursos</Link>
        </section> : <>
        <section className={`${styles.card} ${styles.paymentCard}`} aria-labelledby="payment-title">
          <div className={styles.sectionHeading}>
            <div>
              <span className={styles.eyebrow}>Assinatura</span>
              <h2 id="payment-title">Pagamento</h2>
            </div>
          </div>
          <div className={styles.paymentFields}>
            <span className={styles.fieldLabel}>CPF</span><span className={styles.readonlyField}>429.***.***-**</span>
            <span className={styles.fieldLabel}>Valor</span><strong className={styles.price}>{currentPlan ? formatPrice(currentPlan.price) : "—"}</strong>
            <span className={styles.fieldLabel}>Cartão</span><span className={styles.readonlyField}>**************</span>
          </div>
          <Link className={styles.primaryButton} href="/assinatura">Gerenciar pagamento</Link>
        </section>

        <section className={`${styles.card} ${styles.planCard}`} aria-labelledby="plan-title">
          <span className={styles.eyebrow}>{currentPlan?.status === "active" ? "Plano atual" : "Acesso demonstrativo"}</span>
          <h2 id="plan-title">{accessError ? "Acessos indisponíveis" : !accessReady ? "Consultando acessos..." : currentPlan?.plan === "complete" ? "Assinatura completa" : currentPlan ? "Curso individual" : "Nenhum plano ativo"}</h2>
          {accessError && <p role="alert">{accessError}</p>}
          <ul>
            <li><span className={styles.check}><Icon name="check" /></span>Acesso vitalício à matéria escolhida</li>
            <li><span className={styles.check}><Icon name="check" /></span>Videoaulas e material complementar</li>
            <li><span className={styles.check}><Icon name="check" /></span>Certificado de conclusão da matéria</li>
          </ul>
          <Link className={styles.secondaryButton} href="/planos">Ver outros planos</Link>
        </section>
        </>}
      </div>
      {notice && <div className={styles.notice} role="status">{notice}</div>}
    </div>
  );
}
