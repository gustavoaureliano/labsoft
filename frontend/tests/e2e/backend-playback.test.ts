import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("o aluno reproduz um vídeo real, busca posição e retoma após recarregar", {skip: process.env.E2E_BACKEND !== "true"}, async () => {
  await withBrowser(async driver => {
    await driver.get(`${baseUrl}/videoaula?aula=demo-quantica-introducao`);
    const video = await driver.wait(until.elementLocated(By.css("video")), 10000);
    await driver.wait(async () => driver.executeScript<boolean>("return arguments[0].readyState >= 1", video), 10000);
    await video.click();
    await driver.executeScript("arguments[0].currentTime = 2; return arguments[0].play();", video);
    await driver.wait(async () => driver.executeScript<boolean>("return arguments[0].currentTime > 3", video), 10000);
    await driver.executeScript("arguments[0].pause(); arguments[0].currentTime = 6; arguments[0].dispatchEvent(new Event('pause'));", video);
    await driver.wait(until.elementLocated(By.xpath("//small[contains(., 'Progresso salvo: 6s')]")), 10000);
    await driver.navigate().refresh();
    const resumed = await driver.wait(until.elementLocated(By.css("video")), 10000);
    await driver.wait(async () => driver.executeScript<boolean>("return arguments[0].readyState >= 1 && arguments[0].currentTime >= 5.5", resumed), 10000);
    const paused = await driver.executeScript<boolean>("return arguments[0].paused", resumed);
    assert.equal(paused, true);
    const result = await driver.executeAsyncScript<{status: number; range: string}>(`const done = arguments[arguments.length - 1]; fetch(document.querySelector('video').getAttribute('src'), {headers: {Range: 'bytes=0-15'}}).then(r => done({status: r.status, range: r.headers.get('content-range')}));`);
    assert.equal(result.status, 206);
    assert.match(result.range, /^bytes 0-15\//);
  });
});

test("o aluno sem matrícula não contorna acesso pela URL direta do vídeo", {skip: process.env.E2E_BACKEND !== "true"}, async () => {
  await withBrowser(async driver => {
    await driver.get(`${baseUrl}/videoaula?aula=demo-quantica-introducao`);
    const video = await driver.wait(until.elementLocated(By.css("video")), 10000);
    const url = await video.getAttribute("src");
    await driver.executeScript("document.cookie = 'aprovaai_demo_user=aluno-demo-2; Path=/; SameSite=Lax'");
    const status = await driver.executeAsyncScript<number>("const url = arguments[0], done = arguments[arguments.length - 1]; fetch(url, {headers: {Range: 'bytes=0-15'}}).then(r => done(r.status));", url);
    assert.equal(status, 403);
    await driver.navigate().refresh();
    await driver.wait(until.elementLocated(By.css('[role="alert"]')), 10000);
    assert.equal((await driver.findElements(By.css("video"))).length, 0);
  });
});
