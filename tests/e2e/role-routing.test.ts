import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("a landing é pública e páginas internas exigem um perfil demo", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    assert.match(await driver.findElement(By.css("h1")).getText(), /Estude com foco no vestibular/);
    assert.equal((await driver.findElements(By.css('nav[aria-label="Acesso à conta"] a'))).length, 2);
    await driver.get(`${baseUrl}/meus-cursos`);
    await driver.wait(until.urlContains("/login"), 10000);
    await driver.get(`${baseUrl}/admin`);
    await driver.wait(until.urlContains("/login"), 10000);
  }, null);
});

test("o aluno vê seu menu e não entra na área do professor", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    const navigation = await driver.findElement(By.css('nav[aria-label="Navegação principal"]'));
    assert.equal(await driver.findElement(By.css('header a[aria-label="Ir para a página inicial da AprovaAí"]')).getAttribute("href"), `${baseUrl}/`);
    assert.equal((await navigation.findElements(By.css('a[href="/professor/duvidas"]'))).length, 0);
    assert.equal((await navigation.findElements(By.css('a[href="/duvidas"]'))).length, 1);
    await driver.get(`${baseUrl}/professor/cursos`);
    await driver.wait(until.urlIs(`${baseUrl}/`), 10000);
    await driver.get(`${baseUrl}/duvidas/aluno`);
    await driver.wait(until.urlIs(`${baseUrl}/duvidas`), 10000);
    await pauseForReview();
  });
});

test("professor e admin recebem seus próprios menus e destinos", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    await driver.wait(until.urlContains("/professor/cursos"), 10000);
    assert.equal(await driver.findElement(By.css('header a[aria-label="Ir para a página inicial da AprovaAí"]')).getAttribute("href"), `${baseUrl}/professor/cursos`);
    assert.equal((await driver.findElements(By.css('nav[aria-label="Navegação do professor"] a[href="/professor/duvidas"]'))).length, 1);
    await driver.get(`${baseUrl}/duvidas`);
    await driver.wait(until.urlContains("/professor/cursos"), 10000);
    await driver.get(`${baseUrl}/admin`);
    await driver.wait(until.urlContains("/professor/cursos"), 10000);
  }, "teacher");

  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    await driver.wait(until.urlIs(`${baseUrl}/admin`), 10000);
    assert.equal(await driver.findElement(By.css('header a[aria-label="Ir para a página inicial da AprovaAí"]')).getAttribute("href"), `${baseUrl}/admin`);
    assert.equal((await driver.findElements(By.css('nav[aria-label="Navegação administrativa"] a[href="/admin/moderacao"]'))).length, 1);
    await driver.get(`${baseUrl}/meus-cursos`);
    await driver.wait(until.urlIs(`${baseUrl}/admin`), 10000);
    await driver.findElement(By.css('details[aria-label="Conta de demonstração"] summary')).click();
    await driver.findElement(By.xpath('//button[normalize-space()="Sair"]')).click();
    await driver.wait(until.urlIs(`${baseUrl}/`), 10000);
    await driver.wait(until.elementLocated(By.xpath('//h1[contains(normalize-space(),"Estude com foco no vestibular")]')), 10000);
    await driver.get(`${baseUrl}/admin`);
    await driver.wait(until.urlContains("/login"), 10000);
  }, "admin");
});

test("o login demo abre a área escolhida para professor e admin", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/login`);
    await driver.findElement(By.css('input[name="email"]')).sendKeys("professor@exemplo.com");
    await driver.findElement(By.css('input[name="password"]')).sendKeys("demo");
    await driver.findElement(By.css("select")).sendKeys("Professor");
    await driver.findElement(By.css('button[type="submit"]')).click();
    await driver.wait(until.urlContains("/professor/cursos"), 10000);

    await driver.findElement(By.css('details[aria-label="Conta de demonstração"] summary')).click();
    await driver.findElement(By.linkText("Trocar perfil")).click();
    await driver.wait(until.urlContains("/login"), 10000);
    await driver.findElement(By.css('input[name="email"]')).sendKeys("admin@exemplo.com");
    await driver.findElement(By.css('input[name="password"]')).sendKeys("demo");
    await driver.findElement(By.css("select")).sendKeys("Administrador");
    await driver.findElement(By.css('button[type="submit"]')).click();
    await driver.wait(until.urlIs(`${baseUrl}/admin`), 10000);
  }, null);
});
