import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { Browser, Builder, type WebDriver } from "selenium-webdriver";

type DemoRole = "student" | "teacher" | "admin";
const demoRoleCookieName = "aprovaai_demo_role";
const roleToDemoUser: Record<DemoRole, string> = {
  student: "aluno-demo",
  teacher: "professor-demo",
  admin: "admin-demo",
};

const require = createRequire(import.meta.url);
const chrome = require("selenium-webdriver/chrome") as typeof import("selenium-webdriver/chrome");

export const baseUrl = process.env.BASE_URL ?? "http://localhost:3000";
const reviewDelay = Number(process.env.E2E_SLOW_MS ?? 0);

export function pauseForReview() {
  return reviewDelay > 0 ? new Promise((resolve) => setTimeout(resolve, reviewDelay)) : Promise.resolve();
}

export async function setDemoRoleForTest(driver: WebDriver, role: DemoRole | null) {
  if (role) {
    await driver.manage().addCookie({ name: demoRoleCookieName, value: role, path: "/" });
    await driver.manage().addCookie({ name: "aprovaai_demo_user", value: roleToDemoUser[role], path: "/" });
  } else {
    await driver.manage().deleteCookie(demoRoleCookieName);
    await driver.manage().deleteCookie("aprovaai_demo_user");
  }
}

export async function withBrowser(run: (driver: WebDriver) => Promise<void>, role: DemoRole | null = "student") {
  const options = new chrome.Options();
  options.addArguments("--window-size=1440,900");
  if (process.env.E2E_HEADLESS !== "false") {
    options.addArguments("--headless=new", "--no-sandbox", "--disable-dev-shm-usage");
  }

  const chromeBinary = process.env.CHROME_BINARY ?? "/usr/bin/chromium";
  if (existsSync(chromeBinary)) options.setChromeBinaryPath(chromeBinary);

  const resetRes = await fetch(`${baseUrl}/api/testing/reset`, { method: "POST" });
  if (!resetRes.ok) {
    throw new Error(`Falha ao resetar banco de testes via /api/testing/reset: ${resetRes.status}`);
  }

  const driver = await new Builder().forBrowser(Browser.CHROME).setChromeOptions(options).build();

  try {
    await driver.get(`${baseUrl}/login`);
    await setDemoRoleForTest(driver, role);
    await run(driver);
  } finally {
    await driver.quit();
  }
}
