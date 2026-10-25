import assert from "node:assert/strict";
import { test } from "node:test";
import { By, Key, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("cards de certificados distinguem conclusão, andamento e acesso restrito", { skip: process.env.E2E_BACKEND !== "true" }, async () => {
  await withBrowser(async driver => {
    await driver.get(`${baseUrl}/certificados`);
    await driver.wait(until.elementLocated(By.id("ready-title")), 10000);
    const ready = await driver.findElements(By.css('button[aria-label^="Emitir certificado de "]'));
    if (ready.length) {
      const card = await ready[0].findElement(By.xpath("./ancestor::article"));
      const buttonRect = await ready[0].getRect();
      const cardRect = await card.getRect();
      assert.ok(Math.abs(buttonRect.width - cardRect.width) <= 2);
      assert.ok(Math.abs(buttonRect.height - cardRect.height) <= 2);
      assert.match(await card.getText(), /Pronto para emitir/i);
    }

    const studying = await driver.findElement(By.xpath('//section[@aria-labelledby="studying-title"]//article[.//h3[contains(normalize-space(), "Biologia Celular")]]'));
    const link = await studying.findElement(By.css("a"));
    assert.match(await link.getAttribute("href") ?? "", /\/meus-cursos\/biologia-celular$/);
    await link.sendKeys(Key.ENTER);
    await driver.wait(until.urlContains("/meus-cursos/biologia-celular"), 10000);

    await driver.manage().addCookie({ name: "aprovaai_demo_user", value: "aluno-acesso-demo", path: "/" });
    await driver.get(`${baseUrl}/certificados`);
    const restricted = await driver.wait(until.elementLocated(By.xpath('//section[@aria-labelledby="restricted-title"]//article[.//h3[normalize-space()="Introdução à Física Quântica"]]')), 10000);
    assert.match(await restricted.getText(), /Acesso expirado/i);
    assert.match(await restricted.findElement(By.css("a")).getAttribute("href") ?? "", /\/cursos\/fisica-quantica$/);
    assert.equal((await restricted.findElements(By.css('button[aria-label^="Emitir certificado"]'))).length, 0);
  });
});
