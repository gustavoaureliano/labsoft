import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { Browser, Builder, type WebDriver } from "selenium-webdriver";

type DemoRole = "student" | "teacher" | "admin";
const demoRoleCookieName = "aprovaai_demo_role";

const require = createRequire(import.meta.url);
const chrome = require("selenium-webdriver/chrome") as typeof import("selenium-webdriver/chrome");

export const baseUrl = process.env.BASE_URL ?? "http://localhost:3000";
const reviewDelay = Number(process.env.E2E_SLOW_MS ?? 0);

export function pauseForReview() {
  return reviewDelay > 0 ? new Promise((resolve) => setTimeout(resolve, reviewDelay)) : Promise.resolve();
}

export async function setDemoRoleForTest(driver: WebDriver, role: DemoRole | null) {
  if (role) await driver.manage().addCookie({ name: demoRoleCookieName, value: role, path: "/" });
  else await driver.manage().deleteCookie(demoRoleCookieName);
}

export async function withBrowser(run: (driver: WebDriver) => Promise<void>, role: DemoRole | null = "student") {
  const options = new chrome.Options();
  options.addArguments("--window-size=1440,900");

  const chromeBinary = process.env.CHROME_BINARY ?? "/usr/bin/chromium";
  if (existsSync(chromeBinary)) options.setChromeBinaryPath(chromeBinary);

  const driver = await new Builder().forBrowser(Browser.CHROME).setChromeOptions(options).build();

  try {
    await driver.get(`${baseUrl}/login`);
    await setDemoRoleForTest(driver, role);
    await run(driver);
  } finally {
    await driver.quit();
  }
}
