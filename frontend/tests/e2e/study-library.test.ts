import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno organiza aulas no histórico, favoritos e playlists", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/meus-cursos`);
    await driver.findElement(By.css('a[href^="/videoaula?"]')).click();
    await driver.wait(until.urlContains("/videoaula"), 10000);
    const favorite = await driver.findElement(By.xpath('//button[contains(normalize-space(),"Salvar nos favoritos")]'));
    await driver.executeScript("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'})", favorite);
    await favorite.click();
    await driver.findElement(By.css('select')).sendKeys("Revisão ENEM");
    await pauseForReview();

    await driver.get(`${baseUrl}/meus-cursos`);
    await driver.wait(until.elementLocated(By.xpath('//strong[normalize-space()="Leis de Newton e suas aplicações"]')), 10000);
    assert.match(await driver.findElement(By.css("main")).getText(), /Leis de Newton/);
    await driver.findElement(By.xpath('//button[normalize-space()="Favoritos"]')).click();
    assert.match(await driver.findElement(By.css("main")).getText(), /Leis de Newton/);
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
    assert.equal(await driver.findElement(By.css("h1")).getText(), "Revisão ENEM");
    assert.match(await driver.findElement(By.css("main")).getText(), /Leis de Newton/);
  });
});
