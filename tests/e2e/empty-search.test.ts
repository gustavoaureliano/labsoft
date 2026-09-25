import { test } from "node:test";
import { By, Key, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("o aluno se recupera de uma busca sem resultados", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    const globalSearch = await driver.findElement(By.css('form[role="search"] input[name="q"]'));
    await globalSearch.sendKeys("sem-resultados", Key.ENTER);
    await driver.wait(until.urlContains("/pesquisa?q=sem-resultados"), 10000);
    await driver.wait(until.elementLocated(By.xpath('//h2[normalize-space()="Nenhum resultado encontrado"]')), 10000);

    await driver.findElement(By.linkText("Explorar cursos")).click();
    await driver.wait(until.urlContains("/explorar-cursos"), 10000);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Explore cursos"]')), 5000);
  });
});
