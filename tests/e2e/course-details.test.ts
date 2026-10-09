import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno abre um curso e consulta seus detalhes antes de escolher o acesso", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/explorar-cursos`);
    await driver.findElement(By.css('a[aria-label="Ver detalhes de Introdução à Física Quântica"]')).click();
    await driver.wait(until.urlContains("/cursos/fisica-quantica"), 10000);

    assert.equal(await driver.findElement(By.css("h1")).getText(), "Introdução à Física Quântica");
    assert.match(await driver.findElement(By.css("main")).getText(), /Ementa do curso/);
    assert.match(await driver.findElement(By.css("main")).getText(), /Efeito fotoelétrico/);
    assert.match(await driver.findElement(By.css("main")).getText(), /R\$ 29,90/);
    await pauseForReview();

    await driver.findElement(By.linkText("Escolher acesso")).click();
    await driver.wait(until.urlContains("/planos?curso=fisica-quantica"), 10000);
    assert.match(await driver.findElement(By.css("main")).getText(), /Compra individual/i);
    assert.match(await driver.findElement(By.css("main")).getText(), /Assinatura completa/i);
  });
});

test("o aluno continua um curso em que já está matriculado", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/cursos/fisica-enem-mecanica`);
    const continueLink = await driver.wait(until.elementLocated(By.linkText("Continuar curso")), 10000);
    assert.equal(await continueLink.getAttribute("href"), `${baseUrl}/meus-cursos/fisica-enem-mecanica`);
    assert.match(await driver.findElement(By.css('aside[aria-label="Opções de acesso"]')).getText(), /68% concluído/);
  });
});
