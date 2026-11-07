import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("o aluno encontra a continuação na home e consulta seus cursos reais", async () => {
  await withBrowser(async driver => {
    await driver.get(baseUrl);
    await driver.wait(until.elementLocated(By.css('section[aria-labelledby="continue-title"] a[aria-label^="Continuar aula"]')), 10000);
    assert.match(await driver.findElement(By.css("main")).getText(), /Outras formas de estudar/);
    await driver.findElement(By.linkText("Ver aulas do curso →")).click();
    await driver.wait(until.elementLocated(By.id("course-content-title")), 10000);
    assert.ok((await driver.findElements(By.css('section[aria-labelledby="course-content-title"] li'))).length >= 2);
    await driver.get(`${baseUrl}/meus-cursos`);
    await driver.wait(until.elementLocated(By.css('a[aria-label$=": Introdução à Física Quântica"]')), 10000);
    assert.ok(await driver.findElement(By.css('a[aria-label$=": Física para o ENEM: Mecânica"]')).isDisplayed());
  });
});
