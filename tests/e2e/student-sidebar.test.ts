import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("o aluno recolhe o menu e mantém sua escolha ao navegar", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    await driver.findElement(By.css('button[aria-label="Recolher menu"]')).click();
    await driver.findElement(By.linkText("Ver meus cursos")).click();
    await driver.wait(until.urlContains("/meus-cursos"), 10000);

    const expandButton = await driver.wait(until.elementLocated(By.css('button[aria-label="Expandir menu"]')), 5000);
    assert.equal(await expandButton.getAttribute("aria-expanded"), "false");

    await driver.navigate().refresh();
    const persistedMenu = await driver.wait(until.elementLocated(By.css('button[aria-label="Expandir menu"]')), 5000);
    assert.equal(await persistedMenu.getAttribute("aria-expanded"), "false");
  });
});
