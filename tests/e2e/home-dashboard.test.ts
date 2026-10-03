import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("o aluno explora a home e encontra formas de estudar", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    const homeText = await driver.findElement(By.css("main")).getText();
    assert.match(homeText, /Exercícios de dinâmica/);
    assert.match(homeText, /História do Brasil em perspectiva/);
    assert.match(homeText, /Outras formas de estudar/);
    assert.equal(await driver.executeScript("return document.documentElement.scrollHeight > innerHeight"), true);

    await driver.findElement(By.linkText("Ver aulas do curso →")).click();
    await driver.wait(until.urlContains("/videoaula"), 10000);
  });
});
