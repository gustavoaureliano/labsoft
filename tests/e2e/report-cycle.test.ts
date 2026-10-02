import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno denuncia uma aula uma vez e a moderação registra a decisão", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/videoaula`);
    await driver.findElement(By.css("#lesson-report")).sendKeys("Áudio indisponível");
    const submit = await driver.findElement(By.xpath('//button[normalize-space()="Enviar denúncia"]'));
    await driver.executeScript("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'})", submit);
    await submit.click();
    assert.match(await driver.findElement(By.css('[role="tabpanel"]')).getText(), /Denúncia enviada para análise/);
    assert.equal(await driver.findElement(By.css("#lesson-report")).isEnabled(), false);
    await pauseForReview();

    await driver.get(`${baseUrl}/admin/moderacao`);
    const report = await driver.wait(until.elementLocated(By.xpath('//li[contains(.,"Áudio indisponível")]')), 10000);
    const keep = await report.findElement(By.xpath('.//button[normalize-space()="Manter conteúdo"]'));
    await driver.executeScript("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'})", keep);
    await keep.click();
    assert.match(await report.getText(), /conteúdo mantido/);
    await driver.get(`${baseUrl}/videoaula`);
    assert.match(await driver.findElement(By.css('[role="tabpanel"]')).getText(), /conteúdo mantido/);
  });
});
