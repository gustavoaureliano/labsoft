import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("o aluno continua uma aula real pela Home e pausa o vídeo", async () => {
  await withBrowser(async driver => {
    await driver.get(baseUrl);
    const card = await driver.wait(until.elementLocated(By.css('a[aria-label^="Continuar aula"]')), 10000);
    const href = await card.getAttribute("href");
    assert.ok(href);
    assert.match(href, /\/videoaula\?aula=/);
    await card.click();
    const video = await driver.wait(until.elementLocated(By.css("video")), 10000);
    await driver.wait(async () => driver.executeScript<boolean>("return arguments[0].readyState >= 1", video), 10000);
    await video.click();
    await driver.executeScript("arguments[0].currentTime = 1; return arguments[0].play();", video);
    await driver.wait(async () => driver.executeScript<boolean>("return arguments[0].currentTime > 1.5", video), 10000);
    await driver.executeScript("arguments[0].pause()", video);
    assert.equal(await driver.executeScript("return arguments[0].paused", video), true);
  });
});
