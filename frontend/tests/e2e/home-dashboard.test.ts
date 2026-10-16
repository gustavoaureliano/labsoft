import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("o aluno explora a home e encontra formas de estudar", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    const homeText = await driver.findElement(By.css("main")).getText();
    assert.match(homeText, /Exercícios de dinâmica/);
    assert.match(homeText, /História do Brasil em perspectiva/);
    assert.match(homeText, /Outras formas de estudar/);
    const recommendations = await driver.findElement(By.css('section[aria-labelledby="recommended-title"]'));
    assert.doesNotMatch(await recommendations.getText(), /Física para o ENEM: Mecânica/);
    assert.equal(await driver.executeScript("return document.documentElement.scrollHeight > innerHeight"), true);

    await driver.findElement(By.xpath('//aside[@aria-label="Outras aulas do curso"]//strong[normalize-space()="Exercícios de dinâmica"]/ancestor::a')).click();
    await driver.wait(until.urlContains("aula=exercicios-dinamica"), 10000);
    assert.equal(await driver.findElement(By.css("h1")).getText(), "Exercícios de dinâmica");

    await driver.get(baseUrl);
    await driver.findElement(By.linkText("Ver aulas do curso →")).click();
    await driver.wait(until.urlContains("/meus-cursos/fisica-enem-mecanica"), 10000);
    assert.equal((await driver.findElements(By.css('section[aria-labelledby="course-content-title"] ol li'))).length, 12);
  });
});
