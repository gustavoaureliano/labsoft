import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno envia uma dúvida geral pela página do curso", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/meus-cursos/fisica-enem-mecanica`);
    await driver.findElement(By.linkText("Tirar dúvida sobre este curso")).click();
    await driver.wait(until.urlContains("/duvidas?curso=fisica-enem-mecanica"), 10000);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Enviar nova dúvida ao professor"]')), 10000);
    await pauseForReview();

    const courseSelect = await driver.findElement(By.css('select[name="course"]'));
    const lessonSelect = await driver.findElement(By.css('select[name="lesson"]'));
    assert.equal(await courseSelect.getAttribute("value"), "fisica-enem-mecanica");
    assert.equal(await lessonSelect.getAttribute("value"), "");

    await driver.findElement(By.css("textarea#question-text")).sendKeys("Qual conteúdo devo revisar primeiro para acompanhar o curso?");
    await driver.findElement(By.xpath('//button[normalize-space()="Enviar Pergunta"]')).click();
    await driver.wait(until.elementLocated(By.xpath('//*[@role="status" and normalize-space()="Sua dúvida foi enviada ao professor."]')), 5000);
    const latestDiscussion = await driver.findElement(By.css("article"));
    assert.match(await latestDiscussion.getText(), /Pendente[\s\S]*Física para o ENEM: Mecânica[\s\S]*Dúvida geral sobre o curso[\s\S]*Qual conteúdo devo revisar/);
    await pauseForReview();
  });
});
