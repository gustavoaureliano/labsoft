import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno continua a aula e a encontra no histórico, favoritos e playlist", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/meus-cursos`);
    await driver.findElement(By.css('a[href="/videoaula"]')).click();
    await driver.wait(until.urlContains("/videoaula"), 10000);
    const favorite = await driver.findElement(By.xpath('//button[contains(normalize-space(),"Salvar nos favoritos")]'));
    await favorite.click();
    await driver.findElement(By.css('select')).sendKeys("Revisão ENEM");
    await pauseForReview();

    await driver.get(`${baseUrl}/meus-cursos`);
    await driver.wait(until.elementLocated(By.xpath('//p[contains(.,"Assistido recentemente")]')), 10000);
    await driver.findElement(By.xpath('//button[normalize-space()="Favoritos"]')).click();
    assert.match(await driver.findElement(By.css("main")).getText(), /Leis de Newton/);
    await driver.findElement(By.xpath('//button[normalize-space()="Playlists"]')).click();
    assert.match(await driver.findElement(By.css("main")).getText(), /Revisão ENEM/);
    assert.match(await driver.findElement(By.css("main")).getText(), /Leis de Newton/);
    await driver.findElement(By.css("#playlist-name")).sendKeys("Revisão de Física");
    await driver.findElement(By.xpath('//button[normalize-space()="Criar playlist"]')).click();
    assert.match(await driver.findElement(By.css("main")).getText(), /Revisão de Física/);
  });
});
