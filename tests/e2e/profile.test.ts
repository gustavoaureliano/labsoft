import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno salva o apelido no perfil deste navegador", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    await driver.findElement(By.linkText("Meu perfil")).click();
    await driver.wait(until.urlContains("/perfil"), 10000);
    await pauseForReview();

    const nickname = await driver.wait(until.elementLocated(By.css('input[name="nickname"]')), 10000);
    await nickname.clear();
    await nickname.sendKeys("Aluno Selenium");
    await driver.findElement(By.xpath('//button[normalize-space()="Salvar modificações"]')).click();
    await driver.wait(until.elementLocated(By.xpath('//*[@role="status" and contains(., "Modificações salvas")]')), 5000);
    await pauseForReview();

    await driver.navigate().refresh();
    const savedNickname = await driver.wait(until.elementLocated(By.css('input[name="nickname"]')), 10000);
    await driver.wait(async () => (await savedNickname.getAttribute("value")) === "Aluno Selenium", 5000);
    assert.equal(await savedNickname.getAttribute("value"), "Aluno Selenium");
    await pauseForReview();
  });
});
