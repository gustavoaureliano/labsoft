import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { Select } from "selenium-webdriver/lib/select.js";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno explora, filtra e encontra um curso", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    const homeCard = await driver.findElement(By.css('section#meus-cursos article'));
    const homeCardClass = await homeCard.getAttribute("class");
    const homeCardTitle = await homeCard.findElement(By.css("h3")).getText();
    assert.equal(homeCardTitle, "Introdução à Física Quântica");
    await driver.findElement(By.linkText("Explorar todos")).click();
    await driver.wait(until.urlContains("/explorar-cursos"), 10000);
    await pauseForReview();

    const results = await driver.wait(until.elementLocated(By.css('section[aria-labelledby="courses-title"]')), 10000);
    const exploreCardClass = await results.findElement(By.css("article")).getAttribute("class");
    assert.equal(exploreCardClass, homeCardClass);
    assert.equal(await results.findElement(By.css("article h3")).getText(), homeCardTitle);
    const count = await results.findElement(By.css('[aria-live="polite"]'));
    assert.equal(await count.getText(), "6 cursos encontrados");

    await driver.findElement(By.xpath('//button[normalize-space()="Ciências da Natureza"]')).click();
    await driver.wait(until.elementTextIs(count, "3 cursos encontrados"), 5000);
    await pauseForReview();

    await new Select(await driver.findElement(By.css('select[name="sort"]'))).selectByValue("title");
    const firstTitle = await results.findElement(By.css("article h3"));
    await driver.wait(until.elementTextContains(firstTitle, "Biologia Celular"), 5000);

    await driver.findElement(By.xpath('//button[normalize-space()="Todos"]')).click();
    await driver.findElement(By.css('input[name="course-query"]')).sendKeys("estatística");
    await driver.wait(until.elementTextIs(count, "1 curso encontrado"), 5000);
    const cards = await results.findElements(By.css("article"));
    assert.equal(cards.length, 1);
    assert.match(await cards[0].getText(), /Estatística Essencial/);
    await pauseForReview();
  });
});
