import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o professor consulta e ordena cursos sem entrar no editor ainda não integrado", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/professor/cursos`);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Gestão de cursos"]')), 10000);
    const cards = await driver.findElements(By.css("article"));
    assert.ok(cards.length >= 3);
    await driver.findElement(By.xpath('//button[normalize-space()="Aulas"]')).click();
    assert.match(await driver.findElement(By.css("main")).getText(), /Introdução e contexto histórico/);
    await driver.findElement(By.css("select")).sendKeys("Título");
    await driver.findElement(By.xpath('//button[normalize-space()="+ Novo curso"]')).click();
    assert.match(await driver.findElement(By.css('[role="status"]')).getText(), /Editor de Curso.*João/);
    await pauseForReview();
  });
});
