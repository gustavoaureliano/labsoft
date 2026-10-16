import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o professor responde dúvidas e troca para o perfil de aluno", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/professor/duvidas`);
    await driver.wait(until.elementLocated(By.xpath('//span[normalize-space()="Dúvidas dos alunos"]')), 10000);
    await pauseForReview();

    await driver.findElement(By.xpath('//button[contains(normalize-space(),"Pendentes")]')).click();
    const questions = await driver.findElements(By.css("article"));
    assert.equal(questions.length, 2);
    await questions[0].findElement(By.xpath('.//button[normalize-space()="Responder"]')).click();
    await driver.findElement(By.css('textarea[name="answer"]')).sendKeys("A frequência determina a energia de cada fóton.");
    await driver.findElement(By.xpath('//button[normalize-space()="Enviar resposta"]')).click();
    await driver.findElement(By.xpath('//button[contains(normalize-space(),"Respondidas")]')).click();
    await driver.wait(until.elementLocated(By.xpath('//*[normalize-space()="A frequência determina a energia de cada fóton."]')), 5000);
    await pauseForReview();

    const accountMenu = await driver.findElement(By.css('details[aria-label="Conta de demonstração"]'));
    await accountMenu.findElement(By.css("summary")).click();
    await accountMenu.findElement(By.linkText("Trocar perfil")).click();
    await driver.wait(until.urlContains("/login"), 10000);
    await driver.findElement(By.css('input[name="email"]')).sendKeys("aluno@exemplo.com");
    await driver.findElement(By.css('input[name="password"]')).sendKeys("demo");
    await driver.findElement(By.css('button[type="submit"]')).click();
    await driver.wait(until.urlIs(`${baseUrl}/`), 10000);
    await driver.findElement(By.css('nav[aria-label="Navegação principal"] a[href="/duvidas"]')).click();
    await driver.wait(until.urlContains("/duvidas"), 10000);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Enviar nova dúvida ao professor"]')), 10000);
  }, "teacher");
});
