import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("a administração alterna o período dos acessos", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/admin`);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Visão geral do negócio"]')), 10000);
    await pauseForReview();

    const pageText = await driver.findElement(By.css("main")).getText();
    assert.match(pageText, /Faturamento mensal\s+R\$ 84\.500/);
    assert.match(pageText, /Professores cadastrados\s+36/);
    assert.match(pageText, /Alunos cadastrados\s+2\.480/);
    assert.match(pageText, /26\.520\s+acessos no período/);

    const monthly = await driver.findElement(By.xpath('//button[normalize-space()="Mensal"]'));
    assert.equal(await monthly.getAttribute("aria-pressed"), "true");

    const annual = await driver.findElement(By.xpath('//button[normalize-space()="Anual"]'));
    await annual.click();
    await driver.wait(async () => (await annual.getAttribute("aria-pressed")) === "true", 5000);
    assert.equal(await annual.getAttribute("aria-pressed"), "true");
    assert.equal(await monthly.getAttribute("aria-pressed"), "false");
    await driver.wait(until.elementLocated(By.xpath('//*[normalize-space()="Dez"]')), 5000);
    const accessReport = await driver.findElement(By.css('section[aria-labelledby="access-title"]'));
    await driver.wait(async () => (await accessReport.getText()).includes("267.020"), 5000);
    assert.match(await accessReport.getText(), /267\.020\s+acessos no período/);
    await pauseForReview();
  }, "admin");
});
