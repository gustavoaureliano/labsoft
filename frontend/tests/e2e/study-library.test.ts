import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno organiza aulas no histórico, favoritos e playlists", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/meus-cursos`);
    await driver.executeScript("document.documentElement.style.scrollBehavior = 'auto'");
    await (await driver.wait(until.elementLocated(By.css('a[href^="/videoaula?"]')), 10000)).click();
    await driver.wait(until.urlContains("/videoaula"), 10000);
    const favorite = await driver.wait(until.elementLocated(By.xpath('//button[contains(normalize-space(),"Salvar nos favoritos")]')), 10000);
    await driver.executeScript("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'})", favorite);
    await favorite.click();
    await driver.findElement(By.css('select')).sendKeys("Revisão ENEM");
    await pauseForReview();

    await driver.get(`${baseUrl}/meus-cursos`);
    await driver.executeScript("document.documentElement.style.scrollBehavior = 'auto'");
    await driver.wait(until.elementLocated(By.xpath('//strong[normalize-space()="Introdução"]')), 10000);
    assert.match(await driver.findElement(By.css("main")).getText(), /Introdução/);
    await driver.findElement(By.xpath('//button[normalize-space()="Favoritos"]')).click();
    assert.match(await driver.findElement(By.css("main")).getText(), /Introdução/);
    await driver.findElement(By.xpath('//button[normalize-space()="Playlists"]')).click();
    assert.match(await driver.findElement(By.css("main")).getText(), /Revisão ENEM/);
    assert.match(await driver.findElement(By.css("main")).getText(), /1 aula/);
    await driver.findElement(By.css("#playlist-name")).sendKeys("Revisão de Física");
    await driver.findElement(By.xpath('//button[normalize-space()="Criar playlist"]')).click();
    assert.match(await driver.findElement(By.css("main")).getText(), /Revisão de Física/);

    const playlistLink = await driver.findElement(By.xpath('//strong[normalize-space()="Revisão ENEM"]/ancestor::a'));
    await driver.executeScript("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'})", playlistLink);
    await playlistLink.click();
    await driver.wait(until.urlContains("/meus-cursos/playlists/revisao-enem"), 10000);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Revisão ENEM"]')), 10000);
    await driver.wait(until.elementLocated(By.xpath('//strong[normalize-space()="Introdução"]')), 10000);
    assert.match(await driver.findElement(By.css("main")).getText(), /Introdução/);
  });
});
