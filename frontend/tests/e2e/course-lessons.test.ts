import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno abre a página do curso e troca de videoaula", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/videoaula`);
    await driver.findElement(By.css('a[href="/meus-cursos/fisica-enem-mecanica"]')).click();
    await driver.wait(until.urlContains("/meus-cursos/fisica-enem-mecanica"), 10000);
    assert.equal((await driver.findElements(By.css('section[aria-labelledby="course-content-title"] ol li'))).length, 12);
    await pauseForReview();

    const lessonLink = await driver.findElement(By.xpath('//strong[normalize-space()="Exercícios de dinâmica"]/ancestor::a'));
    await driver.executeScript("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'})", lessonLink);
    await lessonLink.click();
    await driver.wait(until.urlContains("aula=exercicios-dinamica"), 10000);
    assert.equal(await driver.findElement(By.css("h1")).getText(), "Exercícios de dinâmica");

    await driver.findElement(By.linkText("Próxima aula →")).click();
    await driver.wait(until.urlContains("aula=trabalho-energia"), 10000);
    assert.equal(await driver.findElement(By.css("h1")).getText(), "Trabalho e energia");
    assert.equal((await driver.findElements(By.xpath('//button[contains(normalize-space(),"favoritos")]'))).length, 1);
    assert.equal((await driver.findElements(By.xpath('//strong[normalize-space()="Área da videoaula"]'))).length, 1);
    await driver.findElement(By.linkText("← Voltar para o curso")).click();
    await driver.wait(until.urlContains("/meus-cursos/fisica-enem-mecanica"), 10000);
  });
});
