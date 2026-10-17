import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno abre um aviso e consulta o estado real dos certificados", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/avisos`);
    const firstNotice = await driver.wait(until.elementLocated(By.xpath('//article[.//h2[normalize-space()="Continue sua aula de Física"]]')), 10000);
    await firstNotice.findElement(By.css('a[href="/videoaula"]')).click();
    await driver.wait(until.urlContains("/videoaula"), 10000);
    await driver.get(`${baseUrl}/avisos`);
    await driver.wait(until.elementLocated(By.xpath('//article[.//h2[normalize-space()="Continue sua aula de Física"]]//span[normalize-space()="Lido"]')), 10000);
    await pauseForReview();

    await driver.get(`${baseUrl}/certificados`);
    await driver.wait(until.elementLocated(By.css("main article")), 10000);
    assert.match(await driver.findElement(By.css("main")).getText(), /Física para o ENEM: Mecânica/);
    assert.doesNotMatch(await driver.findElement(By.css("main")).getText(), /Concluído · exemplo|ilustrativo/);
  });
});
