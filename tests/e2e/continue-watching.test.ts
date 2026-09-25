import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { test } from "node:test";
import { Browser, Builder, By, until } from "selenium-webdriver";
import chrome from "selenium-webdriver/chrome.js";

test("o aluno abre a videoaula e inicia a demonstração", async () => {
  const options = new chrome.Options().addArguments("--window-size=1440,900");
  const chromeBinary = process.env.CHROME_BINARY ?? "/usr/bin/chromium";
  if (existsSync(chromeBinary)) options.setChromeBinaryPath(chromeBinary);

  const driver = await new Builder().forBrowser(Browser.CHROME).setChromeOptions(options).build();

  try {
    await driver.get(process.env.BASE_URL ?? "http://localhost:3000");

    const continueLink = await driver.wait(until.elementLocated(By.linkText("Continuar assistindo")), 10000);
    await continueLink.click();
    await driver.wait(until.urlContains("/videoaula"), 10000);

    const playButton = await driver.wait(until.elementLocated(By.css('button[aria-label="Reproduzir demonstração"]')), 10000);
    await playButton.click();

    const pauseButton = await driver.wait(until.elementLocated(By.css('button[aria-label="Pausar demonstração"]')), 10000);
    assert.equal(await pauseButton.getAttribute("aria-pressed"), "true");
  } finally {
    await driver.quit();
  }
});
