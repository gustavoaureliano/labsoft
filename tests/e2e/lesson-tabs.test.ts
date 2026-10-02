import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno explora as abas da videoaula", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/videoaula`);
    await driver.executeScript("document.documentElement.style.scrollBehavior = 'auto'");
    const panel = await driver.wait(until.elementLocated(By.css('[role="tabpanel"]')), 10000);
    assert.match(await panel.getText(), /Sobre esta aula/);
    await pauseForReview();

    await driver.findElement(By.css('[role="tab"][id="tab-1"]')).click();
    assert.match(await panel.getText(), /Seja o primeiro a comentar/);
    await driver.findElement(By.id("lesson-comment")).sendKeys("Agora entendi a segunda lei!");
    await panel.findElement(By.css('button[type="submit"]')).click();
    assert.match(await panel.getText(), /Agora entendi a segunda lei!/);
    await pauseForReview();

    await driver.findElement(By.css('[role="tab"][id="tab-2"]')).click();
    await driver.findElement(By.id("lesson-note")).sendKeys("Revisar força resultante.");
    await driver.findElement(By.xpath('//button[normalize-space()="Salvar anotação"]')).click();
    assert.match(await panel.getText(), /Anotação salva neste navegador/);
    await pauseForReview();

    await driver.findElement(By.css('[role="tab"][id="tab-3"]')).click();
    await driver.findElement(By.css('button[aria-label="Avaliar com 5 estrelas"]')).click();
    assert.match(await panel.getText(), /Sua avaliação: 5 estrelas/);
    await pauseForReview();

    await driver.findElement(By.css('[role="tab"][id="tab-4"]')).click();
    const materialsLink = await driver.findElement(By.linkText("Explorar materiais →"));
    assert.match((await materialsLink.getAttribute("href")) ?? "", /materiais-complementares/);
    await pauseForReview();
  });
});
