import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("a administração alterna o período dos acessos", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/admin`);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Visão geral do negócio"]')), 10000);
    await pauseForReview();

    const monthly = await driver.findElement(By.xpath('//button[normalize-space()="Mensal"]'));
    assert.equal(await monthly.getAttribute("aria-pressed"), "true");

    const annual = await driver.findElement(By.xpath('//button[normalize-space()="Anual"]'));
    await annual.click();
    await driver.wait(async () => (await annual.getAttribute("aria-pressed")) === "true", 5000);
    assert.equal(await annual.getAttribute("aria-pressed"), "true");
    assert.equal(await monthly.getAttribute("aria-pressed"), "false");
    await driver.wait(until.elementLocated(By.xpath('//*[normalize-space()="Dez"]')), 5000);
    await pauseForReview();
  });
});
