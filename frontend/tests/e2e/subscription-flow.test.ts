import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, resetCommerceState, withBrowser } from "./browser.ts";

// Payment settles asynchronously (mock PSP webhook), so the success screen takes a few seconds.
const settleTimeout = 30000;

beforeEach(resetCommerceState);

test("o aluno contrata uma assinatura demonstrativa e encontra o acesso em Meus Cursos", { timeout: 60000 }, async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/planos?curso=fisica-quantica`);
    await driver.findElement(By.linkText("Escolher assinatura")).click();
    await driver.wait(until.urlContains("/checkout"), 10000);
    assert.match(await driver.findElement(By.css("main")).getText(), /Checkout demonstrativo/i);

    await driver.findElement(By.css('input[name="holder"]')).sendKeys("Aluno Demo");
    await pauseForReview();
    await driver.findElement(By.xpath('//button[normalize-space()="Confirmar acesso demonstrativo"]')).click();
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Pronto para começar"]')), settleTimeout);
    assert.match(await driver.findElement(By.css("main")).getText(), /assinatura demonstrativa está ativa/i);

    await driver.findElement(By.linkText("Ir para Meus Cursos")).click();
    await driver.wait(until.urlContains("/meus-cursos"), 10000);
    assert.match(await driver.findElement(By.css("main")).getText(), /assinatura completa está ativa/i);
  });
});

test("o aluno vê uma compra individual sem controles de assinatura", { timeout: 60000 }, async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/checkout?curso=fisica-quantica&tipo=curso`);
    await driver.findElement(By.css('input[name="holder"]')).sendKeys("Aluno Demo");
    await driver.findElement(By.xpath('//button[normalize-space()="Confirmar acesso demonstrativo"]')).click();
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Pronto para começar"]')), settleTimeout);

    await driver.findElement(By.linkText("Ir para Meus Cursos")).click();
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Meus cursos"]')), 10000);
    assert.equal((await driver.findElements(By.css('a[aria-label="Ver detalhes de Introdução à Física Quântica"]'))).length, 0);

    await driver.get(`${baseUrl}/cursos/fisica-quantica`);
    const accessOptions = await driver.wait(until.elementLocated(By.css('aside[aria-label="Opções de acesso"]')), 10000);
    await driver.wait(until.elementTextContains(accessOptions, "CURSO ADQUIRIDO"), 10000);
    assert.match(await accessOptions.getText(), /Acesso confirmado/);
    assert.equal((await accessOptions.findElements(By.linkText("Escolher acesso"))).length, 0);

    await driver.get(`${baseUrl}/assinatura`);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Acesso individual"]')), 10000);
    assert.match(await driver.findElement(By.css("main")).getText(), /Introdução à Física Quântica/);
    assert.equal((await driver.findElements(By.xpath('//button[contains(normalize-space(),"Cancelar")]'))).length, 0);
  });
});

test("o aluno cancela a assinatura completa e perde o acesso", { timeout: 60000 }, async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/checkout?curso=fisica-quantica&tipo=assinatura`);
    await driver.findElement(By.css('input[name="holder"]')).sendKeys("Aluno Demo");
    await driver.findElement(By.xpath('//button[normalize-space()="Confirmar acesso demonstrativo"]')).click();
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Pronto para começar"]')), settleTimeout);

    await driver.get(`${baseUrl}/assinatura`);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Plano e assinatura"]')), 10000);
    await driver.findElement(By.xpath('//button[normalize-space()="Cancelar plano"]')).click();
    await driver.wait(until.elementLocated(By.linkText("Conhecer planos")), 10000);

    await driver.get(`${baseUrl}/cursos/biologia-celular`);
    const accessOptions = await driver.wait(until.elementLocated(By.css('aside[aria-label="Opções de acesso"]')), 10000);
    await driver.wait(until.elementTextContains(accessOptions, "ACESSO AO CURSO"), 10000);
    assert.equal((await accessOptions.findElements(By.linkText("Escolher acesso"))).length, 1);
  });
});
