import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o visitante simula o acesso e a recuperação sem autenticação real", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/login`);
    await driver.findElement(By.css('input[name="email"]')).sendKeys("aluno@exemplo.com");
    await driver.findElement(By.css('input[name="password"]')).sendKeys("senha-de-teste");
    await driver.findElement(By.css('button[type="submit"]')).click();
    await driver.wait(until.urlIs(`${baseUrl}/`), 10000);
    const account = await driver.executeScript("return JSON.parse(localStorage.getItem('aprovaai-demo-account'))");
    assert.deepEqual(account, { name: "Estudante", email: "aluno@exemplo.com", role: "student" });
    await pauseForReview();

    await driver.get(`${baseUrl}/recuperar-acesso`);
    await driver.findElement(By.css('input[name="email"]')).sendKeys("aluno@exemplo.com");
    await driver.findElement(By.css('button[type="submit"]')).click();
    assert.match(await driver.findElement(By.css('[role="status"]')).getText(), /Nenhum e-mail foi enviado/);
  });
});

test("o professor solicita cadastro e o administrador aprova a demonstração", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/cadastro/professor`);
    await driver.findElement(By.css('input[name="name"]')).sendKeys("Maria Exemplo");
    await driver.findElement(By.css('input[name="email"]')).sendKeys("maria@exemplo.com");
    await driver.findElement(By.css('input[name="area"]')).sendKeys("Física");
    await driver.findElement(By.css('button[type="submit"]')).click();
    await driver.wait(until.urlContains("/professor/solicitacao"), 10000);
    assert.match(await driver.findElement(By.css("main")).getText(), /aguardando análise/);
    await pauseForReview();

    await driver.get(`${baseUrl}/admin/moderacao`);
    const row = await driver.wait(until.elementLocated(By.xpath('//*[contains(@class,"teacherItem")][.//strong[normalize-space()="Maria Exemplo"]]')), 10000);
    await row.findElement(By.xpath('.//button[normalize-space()="Aprovar"]')).click();
    await driver.get(`${baseUrl}/professor/solicitacao`);
    assert.match(await driver.findElement(By.css("main")).getText(), /Aprovad|aprovad/);
  });
});
