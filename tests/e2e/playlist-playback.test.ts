import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno assiste às aulas dentro da ordem de uma playlist", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/videoaula?curso=fisica-enem-mecanica&aula=leis-newton`);
    await driver.findElement(By.css("select")).sendKeys("Revisão ENEM");

    await driver.findElement(By.xpath('//strong[normalize-space()="Exercícios de dinâmica"]/ancestor::a')).click();
    await driver.wait(until.urlContains("aula=exercicios-dinamica"), 10000);
    await driver.findElement(By.css("select")).sendKeys("Revisão ENEM");

    await driver.get(`${baseUrl}/meus-cursos`);
    await driver.findElement(By.xpath('//button[normalize-space()="Playlists"]')).click();
    const playlistLink = await driver.findElement(By.xpath('//strong[normalize-space()="Revisão ENEM"]/ancestor::a'));
    await driver.executeScript("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'})", playlistLink);
    await playlistLink.click();
    await driver.wait(until.urlContains("/meus-cursos/playlists/revisao-enem"), 10000);
    assert.equal((await driver.findElements(By.css('section[aria-labelledby="playlist-lessons-title"] ol li'))).length, 2);
    await pauseForReview();

    await driver.findElement(By.xpath('//strong[normalize-space()="Leis de Newton e suas aplicações"]/ancestor::a')).click();
    await driver.wait(until.urlContains("origem=playlist"), 10000);
    await driver.wait(until.elementTextIs(driver.findElement(By.css("#lessons-title")), "Revisão ENEM"), 10000);
    assert.equal((await driver.findElements(By.css("aside ol li"))).length, 2);

    await driver.findElement(By.linkText("Próxima aula →")).click();
    await driver.wait(until.urlContains("aula=exercicios-dinamica"), 10000);
    assert.equal(await driver.findElement(By.css("h1")).getText(), "Exercícios de dinâmica");
    assert.match(await driver.getCurrentUrl(), /origem=playlist.*lista=revisao-enem/);

    await driver.findElement(By.linkText("← Voltar para a playlist")).click();
    await driver.wait(until.urlContains("/meus-cursos/playlists/revisao-enem"), 10000);
    const removeButtons = await driver.findElements(By.xpath('//button[contains(@aria-label,"Remover")]'));
    await removeButtons[1].click();
    assert.equal((await driver.findElements(By.css('section[aria-labelledby="playlist-lessons-title"] ol li'))).length, 1);
  });
});
