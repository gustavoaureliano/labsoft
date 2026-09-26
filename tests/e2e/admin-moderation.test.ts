import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("a administração aprova um professor pendente na demonstração", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/admin`);
    await driver.findElement(By.linkText("Moderação")).click();
    await driver.wait(until.urlContains("/admin/moderacao"), 10000);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Moderação e qualidade"]')), 10000);
    await pauseForReview();

    const queueCount = await driver.findElement(By.xpath('//h2[normalize-space()="Professores para aprovar"]/following::span[contains(., "pendentes")][1]'));
    assert.equal(await queueCount.getText(), "3 pendentes");

    const ana = await driver.findElement(By.xpath('//li[.//strong[normalize-space()="Ana Beatriz Ribeiro"]]'));
    await ana.findElement(By.xpath('.//button[normalize-space()="Aprovar"]')).click();

    await driver.wait(until.elementLocated(By.xpath('//*[@role="status" and contains(., "Ana Beatriz Ribeiro foi aprovado")]')), 5000);
    await driver.wait(until.elementTextIs(queueCount, "2 pendentes"), 5000);
    assert.equal((await driver.findElements(By.xpath('//li[.//strong[normalize-space()="Ana Beatriz Ribeiro"]]'))).length, 0);
    await pauseForReview();
  });
});
