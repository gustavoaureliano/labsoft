import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno pergunta, o professor responde e o aluno vê a resposta", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/duvidas/aluno`);
    await driver.findElement(By.css("#question-text")).sendKeys("Como aplico a segunda lei de Newton?");
    await driver.findElement(By.xpath('//button[normalize-space()="Enviar Pergunta"]')).click();
    await driver.wait(until.elementLocated(By.xpath('//article[contains(.,"Como aplico a segunda lei de Newton?")]')), 5000);
    await pauseForReview();

    await driver.get(`${baseUrl}/duvidas`);
    const row = await driver.wait(until.elementLocated(By.xpath('//article[contains(.,"Como aplico a segunda lei de Newton?")]')), 10000);
    await row.findElement(By.xpath('.//button[normalize-space()="Responder"]')).click();
    await row.findElement(By.css('textarea[name="answer"]')).sendKeys("Use força resultante igual à massa vezes a aceleração.");
    await row.findElement(By.xpath('.//button[normalize-space()="Enviar resposta"]')).click();

    await driver.get(`${baseUrl}/duvidas/aluno`);
    const answered = await driver.wait(until.elementLocated(By.xpath('//article[contains(.,"Como aplico a segunda lei de Newton?")]')), 10000);
    assert.match(await answered.getText(), /Respondida[\s\S]*Use força resultante igual à massa vezes a aceleração/);
  });
});
