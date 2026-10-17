import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("a playlist mantém ordem entre cursos e não remapeia referências antigas", {skip: process.env.E2E_BACKEND !== "true"}, async () => {
  await withBrowser(async driver => {
    await driver.executeScript(`localStorage.setItem('aprovaai-demo-study', JSON.stringify({viewedLessons: [], favoriteLessons: [], playlists: [{id: 'cross-course', name: 'Revisão entre cursos', lessonIds: ['demo-quantica-introducao', 'old-unknown-id', 'demo-mecanica-vetores']}]}));`);
    await driver.get(`${baseUrl}/meus-cursos/playlists/cross-course`);
    const first = await driver.wait(until.elementLocated(By.css('ol li a[href*="demo-quantica-introducao"]')), 10000);
    assert.match(await driver.findElement(By.css("main")).getText(), /referências antigas/);
    await first.click();
    await driver.wait(until.elementLocated(By.css("video")), 10000);
    assert.ok(await driver.findElement(By.xpath('//aside//h2[normalize-space()="Revisão entre cursos"]')).isDisplayed());
    await driver.findElement(By.linkText("Próxima aula →")).click();
    await driver.wait(until.urlContains("aula=demo-mecanica-vetores"), 10000);
    await driver.wait(until.elementLocated(By.css("video")), 10000);
    assert.match(await driver.findElement(By.css("header h1")).getText(), /Grandezas/);
    assert.equal((await driver.findElements(By.css("video"))).length, 1);
    const stored = await driver.executeScript<string>("return localStorage.getItem('aprovaai-demo-study')");
    assert.ok(stored.includes("old-unknown-id"));
  });
});
