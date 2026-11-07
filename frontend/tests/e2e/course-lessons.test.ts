import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("o aluno abre o curso e troca a videoaula sem duplicar o player", async () => {
  await withBrowser(async driver => {
    await driver.get(`${baseUrl}/meus-cursos/fisica-enem-mecanica`);
    await driver.wait(until.elementLocated(By.id("course-content-title")), 10000);
    const link = await driver.findElement(By.css('section[aria-labelledby="course-content-title"] li a'));
    await driver.executeScript("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'})", link);
    await link.click();
    await driver.wait(until.elementLocated(By.css("video")), 10000);
    await driver.findElement(By.linkText("Próxima aula →")).click();
    await driver.wait(until.urlContains("aula=demo-mecanica-movimento"), 10000);
    await driver.wait(until.elementLocated(By.css("video")), 10000);
    assert.equal((await driver.findElements(By.css("video"))).length, 1);
    assert.equal((await driver.findElements(By.xpath('//button[contains(.,"favoritos")]'))).length, 1);
    await driver.findElement(By.linkText("← Voltar para o curso")).click();
    await driver.wait(until.urlContains("/meus-cursos/fisica-enem-mecanica"), 10000);
  });
});
