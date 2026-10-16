import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, setDemoRoleForTest, withBrowser } from "./browser.ts";

test("o aluno pergunta, o professor responde e o aluno vê a resposta", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/videoaula?curso=fisica-enem-mecanica&aula=leis-newton`);
    await driver.executeScript("document.documentElement.style.scrollBehavior = 'auto'");
    const commentsTab = await driver.findElement(By.css('[role="tab"][id="tab-1"]'));
    await driver.executeScript("arguments[0].scrollIntoView({ block: 'center' })", commentsTab);
    await commentsTab.click();
    const commentsPanel = await driver.findElement(By.css('[role="tabpanel"]'));
    assert.match(await commentsPanel.getText(), /comentários são públicos/i);
    await commentsPanel.findElement(By.linkText("Enviar dúvida ao professor")).click();
    await driver.wait(until.urlContains("/duvidas?curso=fisica-enem-mecanica&aula=leis-newton"), 10000);
    assert.equal(await driver.findElement(By.css('select[name="course"]')).getAttribute("value"), "fisica-enem-mecanica");
    assert.equal(await driver.findElement(By.css('select[name="lesson"]')).getAttribute("value"), "leis-newton");
    await driver.findElement(By.css("#question-text")).sendKeys("Como aplico a segunda lei de Newton?");
    await driver.findElement(By.xpath('//button[normalize-space()="Enviar Pergunta"]')).click();
    await driver.wait(until.elementLocated(By.xpath('//article[contains(.,"Como aplico a segunda lei de Newton?")]')), 5000);
    await pauseForReview();

    await setDemoRoleForTest(driver, "teacher");
    await driver.get(`${baseUrl}/professor/duvidas`);
    const row = await driver.wait(until.elementLocated(By.xpath('//article[contains(.,"Como aplico a segunda lei de Newton?")]')), 10000);
    await row.findElement(By.xpath('.//button[normalize-space()="Responder"]')).click();
    await row.findElement(By.css('textarea[name="answer"]')).sendKeys("Use força resultante igual à massa vezes a aceleração.");
    await row.findElement(By.xpath('.//button[normalize-space()="Enviar resposta"]')).click();

    await setDemoRoleForTest(driver, "student");
    await driver.get(`${baseUrl}/duvidas`);
    const answered = await driver.wait(until.elementLocated(By.xpath('//article[contains(.,"Como aplico a segunda lei de Newton?")]')), 10000);
    assert.match(await answered.getText(), /Respondida[\s\S]*Use força resultante igual à massa vezes a aceleração/);
  });
});
