import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o professor filtra e responde dúvidas e pode trocar para a conta do aluno", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    let accountMenu = await driver.findElement(By.css('details[aria-label="Selecionar conta"]'));
    await accountMenu.findElement(By.css("summary")).click();
    await accountMenu.findElement(By.css("a[href='/duvidas']")).click();
    await driver.wait(until.urlContains("/duvidas"), 10000);
    await driver.wait(until.elementLocated(By.xpath('//strong[normalize-space()="Dúvidas dos Alunos"]')), 10000);
    await pauseForReview();

    accountMenu = await driver.findElement(By.css('details[aria-label="Selecionar conta"]'));
    await accountMenu.findElement(By.css("summary")).click();
    const accounts = await accountMenu.findElements(By.css("a"));
    assert.equal(accounts.length, 2);
    assert.match(await accountMenu.getText(), /Prof\. Fulano[\s\S]*Bob Silva[\s\S]*Estudante FUVEST/);
    await pauseForReview();

    await driver.findElement(By.xpath('//button[normalize-space()="Pendentes (4)"]')).click();
    const questions = await driver.findElements(By.css("article"));
    assert.equal(questions.length, 2);

    await questions[0].findElement(By.xpath('.//button[normalize-space()="Responder"]')).click();
    await driver.findElement(By.css('textarea[name="answer"]')).sendKeys("A frequência determina a energia de cada fóton.");
    await driver.findElement(By.xpath('//button[normalize-space()="Enviar resposta"]')).click();
    await driver.findElement(By.xpath('//button[normalize-space()="Respondidas (12)"]')).click();
    await driver.wait(until.elementLocated(By.xpath('//span[normalize-space()="Respondida"]')), 5000);
    await driver.wait(until.elementLocated(By.xpath('//*[normalize-space()="A frequência determina a energia de cada fóton."]')), 5000);
    await pauseForReview();

    await accountMenu.findElement(By.css("a[href='/duvidas/aluno']")).click();
    await driver.wait(until.urlContains("/duvidas/aluno"), 10000);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Enviar nova dúvida ao professor"]')), 10000);
    await pauseForReview();
  });
});
