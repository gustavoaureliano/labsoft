import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("o aluno conclui o curso e emite um certificado verificável com PDF", {skip: process.env.E2E_BACKEND !== "true"}, async () => {
  await withBrowser(async driver => {
    for (const id of ["demo-mecanica-vetores", "demo-mecanica-movimento"]) {
      await driver.get(`${baseUrl}/videoaula?aula=${id}`);
      const video = await driver.wait(until.elementLocated(By.css("video")), 10000);
      await driver.wait(async () => driver.executeScript<boolean>("return arguments[0].readyState >= 1", video), 10000);
      await video.click();
      await driver.executeScript("arguments[0].currentTime = arguments[0].duration - 0.5; return arguments[0].play();", video);
      await driver.wait(async () => driver.executeScript<boolean>("return arguments[0].ended", video), 10000);
      await driver.wait(until.elementLocated(By.css('small[role="status"]')), 10000);
      await driver.wait(async () => driver.executeAsyncScript<boolean>(`const id = arguments[0], done = arguments[arguments.length - 1]; fetch('/api/learning/lessons/' + id + '/playback').then(r => r.json()).then(r => done(r.completed));`, id), 10000);
    }
    await driver.get(`${baseUrl}/certificados`);
    const course = await driver.wait(until.elementLocated(By.xpath("//article[.//h2[normalize-space()='Física para o ENEM: Mecânica']]")), 10000);
    const buttons = await course.findElements(By.xpath(".//button[normalize-space()='Emitir certificado']"));
    if (buttons.length) await buttons[0].click();
    const link = await driver.wait(until.elementLocated(By.xpath("//article[.//h2[normalize-space()='Física para o ENEM: Mecânica']]//a[contains(., 'Ver certificado')]")), 10000);
    await link.click();
    const pdfLink = await driver.wait(until.elementLocated(By.linkText("Baixar PDF")), 10000);
    const pdfUrl = await pdfLink.getAttribute("href");
    const result = await driver.executeAsyncScript<{status: number; type: string; magic: string}>("const url = arguments[0], done = arguments[arguments.length - 1]; fetch(url).then(async r => done({status: r.status, type: r.headers.get('content-type'), magic: (await r.text()).slice(0,5)}));", pdfUrl);
    assert.equal(result.status, 200); assert.equal(result.type, "application/pdf"); assert.equal(result.magic, "%PDF-");
    const verify = await driver.findElement(By.linkText("Verificar certificado")).getAttribute("href");
    const publicResult = await driver.executeAsyncScript<{course_title: string}>("const url = arguments[0], done = arguments[arguments.length - 1]; fetch(url).then(r => r.json()).then(done);", verify);
    assert.equal(publicResult.course_title, "Física para o ENEM: Mecânica");
  });
});
