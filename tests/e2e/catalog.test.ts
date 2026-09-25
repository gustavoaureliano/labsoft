import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { test } from "node:test";
import { Browser, Builder, By, Key, until, type WebDriver } from "selenium-webdriver";
import chrome from "selenium-webdriver/chrome.js";
import { Select } from "selenium-webdriver/lib/select.js";

async function withBrowser(run: (driver: WebDriver) => Promise<void>) {
  const options = new chrome.Options().addArguments("--window-size=1440,900");
  const chromeBinary = process.env.CHROME_BINARY ?? "/usr/bin/chromium";
  if (existsSync(chromeBinary)) options.setChromeBinaryPath(chromeBinary);

  const driver = await new Builder().forBrowser(Browser.CHROME).setChromeOptions(options).build();

  try {
    await run(driver);
  } finally {
    await driver.quit();
  }
}

const baseUrl = process.env.BASE_URL ?? "http://localhost:3000";

test("explorar cursos filtra por matéria, ordena e busca por texto", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/explorar-cursos`);

    const courseCount = await driver.wait(until.elementLocated(By.css('[aria-live="polite"]')), 10000);
    assert.match(await courseCount.getText(), /6 cursos encontrados/);

    await driver.findElement(By.xpath('//button[normalize-space()="Ciências da Natureza"]')).click();
    await driver.wait(until.elementTextContains(courseCount, "3 cursos encontrados"), 5000);
    await new Select(await driver.findElement(By.css("select"))).selectByValue("title");
    const firstCourse = await driver.findElement(By.css("article h3"));
    await driver.wait(until.elementTextContains(firstCourse, "Biologia Celular"), 5000);

    await driver.findElement(By.xpath('//button[normalize-space()="Todos"]')).click();
    await driver.findElement(By.css('input[placeholder="Ex.: biologia celular"]')).sendKeys("estatística");
    await driver.wait(until.elementTextContains(courseCount, "1 cursos encontrados"), 5000);
    await driver.wait(until.elementLocated(By.xpath('//*[normalize-space()="Estatística Essencial"]')), 5000);
  });
});

test("materiais complementares filtram por curso e tipo", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/materiais-complementares`);

    const materialCount = await driver.findElement(By.css('[aria-live="polite"]'));
    const filters = await driver.findElements(By.css("select"));
    await new Select(filters[0]).selectByVisibleText("Biologia Celular para Vestibulares");
    await driver.wait(until.elementTextContains(materialCount, "2 materiais"), 5000);
    await new Select(filters[1]).selectByVisibleText("Resumo");
    await driver.wait(until.elementTextContains(materialCount, "1 materiais"), 5000);
    await driver.wait(until.elementLocated(By.xpath('//*[normalize-space()="Organelas e suas funções"]')), 5000);
    assert.equal(await driver.findElements(By.xpath('//li[.//*[normalize-space()="Organelas e suas funções"]]')).then((items) => items.length), 1);
  });
});

test("a busca global encontra materiais pelo conteúdo", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/materiais-complementares`);
    const globalSearch = await driver.findElement(By.css('form[role="search"] input[name="q"]'));
    await globalSearch.sendKeys("organelas", Key.ENTER);
    await driver.wait(until.urlContains("/pesquisa?q=organelas"), 10000);
    await driver.wait(until.elementLocated(By.xpath('//*[normalize-space()="Organelas e suas funções"]')), 10000);
    await driver.wait(until.elementLocated(By.xpath('//h2[normalize-space()="Materiais complementares"]')), 5000);
  });
});

test("a busca informa quando não há resultados", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/pesquisa?q=sem-resultados`);
    await driver.wait(until.elementLocated(By.xpath('//*[normalize-space()="Nenhum resultado encontrado"]')), 10000);
    assert.ok(await driver.findElement(By.linkText("Explorar cursos")).isDisplayed());
  });
});