import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("a página de Mecânica agrupa aulas na ordem dos módulos do curso", { skip: process.env.E2E_SHOWCASE !== "true" }, async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/meus-cursos/fisica-enem-mecanica`);
    await driver.wait(until.elementLocated(By.xpath('//section[h3[normalize-space()="Cinemática"]]')), 10000);
    const modules = await driver.findElements(By.xpath('//section[h3 and .//ol]'));
    assert.equal(modules.length, 2);
    assert.deepEqual(await Promise.all(modules.map(async (module) => ({
      title: await module.findElement(By.css("h3")).getText(),
      lessons: (await module.findElements(By.css("ol li"))).length,
    }))), [
      { title: "Cinemática", lessons: 6 },
      { title: "Dinâmica e energia", lessons: 6 },
    ]);
    assert.match(await modules[1].getText(), /Leis de Newton e suas aplicações/);
    assert.ok(await driver.findElement(By.linkText("Continuar na aula 8")).isDisplayed());
  });
});
