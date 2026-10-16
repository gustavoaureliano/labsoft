'use client';

import { startTransition, useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { Avatar } from "./Avatar";
import { Icon } from "./Icons";
import { initialProfile, type Profile } from "../../data/profile";
import styles from "./ProfilePage.module.css";

const storageKey = "aprovaai-profile-demo";

export function ProfilePage() {
  const [form, setForm] = useState<Profile>(initialProfile);
  const [savedName, setSavedName] = useState(initialProfile.nickname);
  const [avatar, setAvatar] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
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

  const save = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
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
            <button type="button" className={styles.avatarButton} onClick={() => fileInput.current?.click()} aria-label="Alterar avatar">
              <Avatar size="large" image={avatar} />
            </button>
          </div>
          <div className={styles.avatarInfo}>
            <span className={styles.eyebrow}>Foto do perfil</span>
            <h2 id="avatar-title">{savedName}</h2>
            <p>Estudante</p>
            <button type="button" className={styles.secondaryButton} onClick={() => fileInput.current?.click()}>Alterar foto</button>
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
          <form onSubmit={save} className={styles.form}>
            <label htmlFor="nickname">Apelido</label>
            <input id="nickname" name="nickname" value={form.nickname} onChange={update("nickname")} required maxLength={60} />

            <label htmlFor="email">Email</label>
            <input id="email" name="email" type="email" value={form.email} onChange={update("email")} required />

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
        <section className={`${styles.card} ${styles.paymentCard}`} aria-labelledby="payment-title">
          <div className={styles.sectionHeading}>
            <div>
              <span className={styles.eyebrow}>Assinatura</span>
              <h2 id="payment-title">Pagamento</h2>
            </div>
          </div>
          <div className={styles.paymentFields}>
            <span className={styles.fieldLabel}>CPF</span><span className={styles.readonlyField}>429.***.***-**</span>
            <span className={styles.fieldLabel}>Valor</span><strong className={styles.price}>R$ 29,90</strong>
            <span className={styles.fieldLabel}>Cartão</span><span className={styles.readonlyField}>**************</span>
          </div>
          <button type="button" className={styles.primaryButton} onClick={() => setNotice("A edição do pagamento precisa ser conectada a um provedor de pagamentos.")}>Alterar dados de pagamento</button>
        </section>

        <section className={`${styles.card} ${styles.planCard}`} aria-labelledby="plan-title">
          <span className={styles.eyebrow}>Plano atual</span>
          <h2 id="plan-title">Curso Individual</h2>
          <ul>
            <li><span className={styles.check}><Icon name="check" /></span>Acesso vitalício à matéria escolhida</li>
            <li><span className={styles.check}><Icon name="check" /></span>Videoaulas e material complementar</li>
            <li><span className={styles.check}><Icon name="check" /></span>Certificado de conclusão da matéria</li>
          </ul>
          <button type="button" className={styles.secondaryButton} onClick={() => setNotice("A lista de planos precisa ser conectada ao catálogo.")}>Ver outros planos</button>
        </section>
      </div>
      {notice && <div className={styles.notice} role="status">{notice}</div>}
    </div>
  );
}
