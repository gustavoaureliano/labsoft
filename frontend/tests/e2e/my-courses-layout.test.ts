import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("Meus Cursos organiza cards em três, duas ou uma coluna conforme o espaço", async () => {
  await withBrowser(async (driver) => {
    for (const [width, expectedColumns] of [[1600, 3], [1180, 2], [700, 1], [390, 1]]) {
      await driver.manage().window().setRect({ width, height: 900 });
      await driver.get(`${baseUrl}/meus-cursos`);
      const cards = await driver.wait(
        until.elementsLocated(By.css('section[aria-labelledby="in-progress-title"] article')),
        10000,
      );
      assert.ok(cards.length >= 2);
      const columns = await driver.executeScript<number>(
        "return getComputedStyle(document.querySelector('section[aria-labelledby=\"in-progress-title\"] div[class*=\"courseGrid\"]')).gridTemplateColumns.split(' ').length",
      );
      assert.equal(columns, expectedColumns, `Número de colunas com ${width}px`);
      assert.equal(await driver.executeScript<boolean>("return document.documentElement.scrollWidth > innerWidth"), false);
      for (const card of cards) {
        assert.equal((await card.findElements(By.css("a"))).length, 1, "Cada card deve ter um único link");
      }
    }

    await driver.manage().window().setRect({ width: 1180, height: 900 });
    await driver.get(`${baseUrl}/meus-cursos`);
    const toggle = await driver.wait(until.elementLocated(By.css('button[aria-label="Recolher menu"]')), 10000);
    await toggle.click();
    await driver.wait(async () => driver.executeScript<number>(
      "return getComputedStyle(document.querySelector('section[aria-labelledby=\"in-progress-title\"] div[class*=\"courseGrid\"]')).gridTemplateColumns.split(' ').length",
    ).then((columns) => columns === 3), 10000);
  });
});
