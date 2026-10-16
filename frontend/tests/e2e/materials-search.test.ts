import assert from "node:assert/strict";
import { test } from "node:test";
import { By, Key, until } from "selenium-webdriver";
import { Select } from "selenium-webdriver/lib/select.js";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno filtra materiais e encontra um resumo pela busca", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    await driver.findElement(By.linkText("Materiais")).click();
    await driver.wait(until.urlContains("/materiais-complementares"), 10000);
    await pauseForReview();

    const count = await driver.wait(until.elementLocated(By.css('[aria-live="polite"]')), 10000);
    await new Select(await driver.findElement(By.css('select[name="course-filter"]'))).selectByVisibleText("Biologia Celular para Vestibulares");
    await driver.wait(until.elementTextIs(count, "2 materiais"), 5000);
    await new Select(await driver.findElement(By.css('select[name="type-filter"]'))).selectByVisibleText("Resumo");
    await driver.wait(until.elementTextIs(count, "1 material"), 5000);
    assert.equal((await driver.findElements(By.css('section[aria-labelledby="course-biologia-celular"] li'))).length, 1);
    await driver.wait(until.elementLocated(By.xpath('//h3[normalize-space()="Organelas e suas funções"]')), 5000);
    await pauseForReview();

    const globalSearch = await driver.findElement(By.css('form[role="search"] input[name="q"]'));
    await globalSearch.sendKeys("organelas", Key.ENTER);
    await driver.wait(until.urlContains("/pesquisa?q=organelas"), 10000);
    await driver.wait(until.elementLocated(By.xpath('//h2[normalize-space()="Materiais complementares"]')), 10000);
    await driver.wait(until.elementLocated(By.xpath('//h3[normalize-space()="Organelas e suas funções"]')), 5000);
    await pauseForReview();
  });
});
