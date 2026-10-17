import assert from "node:assert/strict";
import { test } from "node:test";
import { By, Key, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("o professor cria aula, envia vídeo real, visualiza e exclui sem apagar o arquivo", {skip: process.env.E2E_BACKEND !== "true"}, async () => {
  assert.ok(process.env.E2E_VIDEO_PATH, "Set E2E_VIDEO_PATH to the generated test MP4");
  await withBrowser(async driver => {
    await driver.get(`${baseUrl}/professor/cursos/fisica-quantica/editar`);
    await driver.executeScript("document.documentElement.style.scrollBehavior = 'auto'");
    const add = await driver.wait(until.elementLocated(By.xpath("//button[normalize-space()='+ Adicionar aula']")), 10000);
    await driver.wait(until.elementIsEnabled(add), 10000);
    const count = (await driver.findElements(By.css('article[aria-label^="Aula "]'))).length;
    await add.click();
    await driver.wait(async () => (await driver.findElements(By.css('article[aria-label^="Aula "]'))).length === count + 1, 10000);
    const rowSelector = `article[aria-label="Aula ${count + 1}"]`;
    const title = `Aula Selenium ${Date.now()}`;
    let row = await driver.findElement(By.css(rowSelector));
    const input = await row.findElement(By.css("input:not([type=file])"));
    await input.sendKeys(Key.CONTROL, "a", Key.NULL, title);
    await row.findElement(By.xpath(".//button[normalize-space()='Salvar aula']")).click();
    await driver.wait(until.elementLocated(By.xpath(`//h3[contains(., '${title}')]`)), 10000);
    row = await driver.findElement(By.css(rowSelector));
    await row.findElement(By.css('input[accept="video/mp4,video/webm"]')).sendKeys(process.env.E2E_VIDEO_PATH!);
    await driver.wait(until.elementLocated(By.css(`${rowSelector} button`)), 10000);
    await driver.wait(until.elementLocated(By.xpath(`//article[@aria-label='Aula ${count + 1}']//button[normalize-space()='Prévia da aula']`)), 15000);
    row = await driver.findElement(By.css(rowSelector));
    await row.findElement(By.xpath(".//button[normalize-space()='Prévia da aula']")).click();
    const video = await driver.wait(until.elementLocated(By.css(`${rowSelector} video`)), 10000);
    await driver.wait(async () => driver.executeScript<boolean>("return arguments[0].readyState >= 1", video), 10000);
    const videoUrl = await video.getAttribute("src");
    if (process.env.E2E_THUMBNAIL_PATH) {
      row = await driver.findElement(By.css(rowSelector));
      await row.findElement(By.css('input[accept="image/png,image/jpeg"]')).sendKeys(process.env.E2E_THUMBNAIL_PATH);
      await driver.wait(until.elementLocated(By.xpath(`//article[@aria-label='Aula ${count + 1}']//button[normalize-space()='Remover thumbnail']`)), 10000);
    }
    await driver.navigate().refresh();
    await driver.executeScript("document.documentElement.style.scrollBehavior = 'auto'");
    await driver.wait(until.elementLocated(By.xpath(`//h3[contains(., '${title}')]`)), 10000);
    row = await driver.findElement(By.css(rowSelector));
    await row.findElement(By.xpath(".//button[normalize-space()='Excluir aula']")).click();
    await driver.switchTo().alert().accept();
    await driver.wait(async () => (await driver.findElements(By.css('article[aria-label^="Aula "]'))).length === count, 10000);
    const status = await driver.executeAsyncScript<number>("const url = arguments[0], done = arguments[arguments.length - 1]; fetch(url, {headers: {Range: 'bytes=0-15'}}).then(r => done(r.status));", videoUrl);
    assert.equal(status, 206, "Deleting the lesson must preserve its owner's video");
  }, "teacher");
});
