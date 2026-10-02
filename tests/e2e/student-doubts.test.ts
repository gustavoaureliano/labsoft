import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { Select } from "selenium-webdriver/lib/select.js";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno envia uma dúvida vinculada a um curso e aula", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/duvidas`);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Enviar nova dúvida ao professor"]')), 10000);
    await pauseForReview();

    const courseSelect = await driver.findElement(By.css('select[name="course"]'));
    await new Select(courseSelect).selectByValue("biologia-celular");
    const lessonSelect = await driver.findElement(By.css('select[name="lesson"]'));
    await driver.wait(async () => (await lessonSelect.getText()).includes("Aula 4 - Organelas Citoplasmáticas"), 5000);
    assert.match(await lessonSelect.getText(), /Aula 4 - Organelas Citoplasmáticas/);
    await new Select(lessonSelect).selectByValue("Aula 4 - Organelas Citoplasmáticas");

    await driver.findElement(By.css("textarea#question-text")).sendKeys("Como diferencio o retículo liso do rugoso na síntese de proteínas?");
    await driver.findElement(By.xpath('//button[normalize-space()="Enviar Pergunta"]')).click();
    await driver.wait(until.elementLocated(By.xpath('//*[@role="status" and normalize-space()="Sua dúvida foi enviada ao professor."]')), 5000);
    const latestDiscussion = await driver.findElement(By.css("article"));
    assert.match(await latestDiscussion.getText(), /Pendente[\s\S]*Biologia Celular para Vestibulares[\s\S]*Aula 4[\s\S]*Como diferencio/);
    await pauseForReview();
  });
});
