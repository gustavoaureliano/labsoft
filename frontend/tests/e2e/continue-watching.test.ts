import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno continua uma aula e alterna o controle de demonstração", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    const homeThumbnail = await driver.findElement(By.css('main img[src*="leis-de-newton"]'));
    assert.equal(await driver.executeScript("return arguments[0].naturalWidth > 0", homeThumbnail), true);
    const continueCard = await driver.findElement(By.css('a[aria-label="Continuar aula Leis de Newton e suas aplicações"]'));
    assert.equal(await continueCard.getAttribute("href"), `${baseUrl}/videoaula?curso=fisica-enem-mecanica&aula=leis-newton`);
    await continueCard.click();
    await driver.wait(until.urlContains("/videoaula"), 10000);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Leis de Newton e suas aplicações"]')), 10000);
    const playerThumbnail = await driver.findElement(By.css('section[aria-label="Videoaula"] img[src*="leis-de-newton"]'));
    assert.equal(await driver.executeScript("return arguments[0].naturalWidth > 0", playerThumbnail), true);
    await pauseForReview();

    const playButton = await driver.wait(until.elementLocated(By.css('button[aria-label="Reproduzir demonstração"]')), 10000);
    await playButton.click();
    const pauseButton = await driver.wait(until.elementLocated(By.css('button[aria-label="Pausar demonstração"]')), 10000);
    assert.equal(await pauseButton.getAttribute("aria-pressed"), "true");
    await pauseForReview();

    await pauseButton.click();
    const resetButton = await driver.wait(until.elementLocated(By.css('button[aria-label="Reproduzir demonstração"]')), 5000);
    assert.equal(await resetButton.getAttribute("aria-pressed"), "false");
    await pauseForReview();
  });
});
