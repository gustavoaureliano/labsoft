import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { Browser, Builder, type WebDriver } from "selenium-webdriver";

const require = createRequire(import.meta.url);
const chrome = require("selenium-webdriver/chrome") as typeof import("selenium-webdriver/chrome");

export const baseUrl = process.env.BASE_URL ?? "http://localhost:3000";

export async function withBrowser(run: (driver: WebDriver) => Promise<void>) {
  const options = new chrome.Options();
  options.addArguments("--window-size=1440,900");

  const chromeBinary = process.env.CHROME_BINARY ?? "/usr/bin/chromium";
  if (existsSync(chromeBinary)) options.setChromeBinaryPath(chromeBinary);

  const driver = await new Builder().forBrowser(Browser.CHROME).setChromeOptions(options).build();

  try {
    await run(driver);
  } finally {
    await driver.quit();
  }
}
