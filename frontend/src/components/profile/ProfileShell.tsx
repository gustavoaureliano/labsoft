"use client";

import { useState } from "react";
import { ProfileLogo } from "./ProfileLogo";
import { navigation } from "../../data/profile";
import { Avatar } from "./Avatar";
import { Icon } from "./Icons";
import styles from "./ProfileShell.module.css";

export function ProfileShell({ children, nickname, avatar, onNavigate }: { children: React.ReactNode; nickname: string; avatar: string | null; onNavigate: (label: string) => void }) {
  const [open, setOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  return <div className={styles.shell}>
    <aside className={`${styles.sidebar} ${open ? styles.open : ""}`} aria-label="Menu principal">
      <div className={styles.brand}><ProfileLogo /></div>
      <nav className={styles.navigation} aria-label="Navegação">
        {navigation.map((item) => <button type="button" key={item.label} aria-current={item.label === "Perfil" ? "page" : undefined}
          className={`${styles.navItem} ${item.label === "Perfil" ? styles.active : ""}`}
          onClick={() => { setOpen(false); if (item.label !== "Perfil") onNavigate(item.label); }}>
          <Icon name={item.icon} /><span>{item.label}</span>
        </button>)}
      </nav>
      <div className={styles.countdown}>
        <strong>ENEM 2026</strong><b>Faltam 241 dias</b><small>Mantenha seu cronograma em dia!</small>
      </div>
    </aside>
    <div className={styles.content}>
      <header className={styles.topbar}>
        <button className={styles.menuButton} type="button" aria-label="Abrir menu" aria-expanded={open} onClick={() => setOpen(!open)}><Icon name="menu" /></button>
        <h1>Seu Perfil</h1>
        <div className={styles.accountWrap}>
          <button className={styles.account} type="button" aria-expanded={accountOpen} onClick={() => setAccountOpen(!accountOpen)}>
            <Avatar image={avatar} /><span><b>{nickname || "Estudante"}</b><small>Estudante FUVEST</small></span><Icon name="chevron" />
          </button>
          {accountOpen && <div className={styles.accountMenu}><span>Minha conta</span><button type="button" onClick={() => setAccountOpen(false)}>Seu Perfil</button></div>}
        </div>
      </header>
      <main className={styles.main}>{children}</main>
    </div>
  </div>;
}
