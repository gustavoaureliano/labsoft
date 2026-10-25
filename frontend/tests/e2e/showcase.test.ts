import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("o cenário completo mostra sete cursos e retoma a aula de Mecânica", {skip: process.env.E2E_SHOWCASE !== "true"}, async () => {
  await withBrowser(async driver => {
    await driver.get(baseUrl);
    const card = await driver.wait(until.elementLocated(By.css('a[aria-label="Continuar aula Leis de Newton e suas aplicações"]')), 10000);
    await card.click();
    const video = await driver.wait(until.elementLocated(By.css("video")), 10000);
    await driver.wait(async () => driver.executeScript<boolean>("return arguments[0].readyState >= 1 && arguments[0].currentTime >= 5.8", video), 10000);
    await video.click();
    await driver.executeScript("return arguments[0].play()", video);
    await driver.wait(async () => driver.executeScript<boolean>("return arguments[0].currentTime > 6.5", video), 10000);
    await driver.executeScript("arguments[0].pause()", video);
    await driver.get(`${baseUrl}/meus-cursos`);
    await driver.wait(async () => (await driver.findElements(By.css('section[aria-labelledby="in-progress-title"] article'))).length === 7, 10000);
    await driver.get(`${baseUrl}/cursos/biologia-celular`);
    const access = await driver.wait(until.elementLocated(By.linkText("Continuar curso")), 10000);
    assert.match((await access.getAttribute("href")) ?? "", /\/meus-cursos\/biologia-celular$/);
    await access.click();
    await driver.wait(async () => (await driver.findElements(By.css('section[aria-labelledby="course-content-title"] li'))).length === 35, 10000);
    await driver.get(`${baseUrl}/certificados`);
    const completed = await driver.wait(until.elementLocated(By.xpath("//article[.//h3[normalize-space()='Redação nota mil: da tese à conclusão']]")), 10000);
    assert.ok(await completed.findElement(By.css('button[aria-label="Emitir certificado de Redação nota mil: da tese à conclusão"]')).isDisplayed());
  });
});
