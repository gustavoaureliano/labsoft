import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o visitante conhece cursos e entra pela landing pública", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    assert.equal(await driver.findElement(By.css("h1")).getText(), "Estude com foco no vestibular e chegue mais longe.");
    assert.equal((await driver.findElements(By.css('section[aria-labelledby="courses-title"] article'))).length, 3);
    await pauseForReview();

    const exploreLink = await driver.findElement(By.linkText("Entre para explorar todos os cursos →"));
    await driver.executeScript("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'})", exploreLink);
    await exploreLink.click();
    await driver.wait(until.urlContains("/login"), 10000);
    await driver.findElement(By.css('input[name="email"]')).sendKeys("aluno@exemplo.com");
    await driver.findElement(By.css('input[name="password"]')).sendKeys("demo");
    await driver.findElement(By.css('button[type="submit"]')).click();
    await driver.wait(until.urlIs(`${baseUrl}/`), 10000);
    await driver.findElement(By.linkText("Explorar todos")).click();
    await driver.wait(until.urlContains("/explorar-cursos"), 10000);
  }, null);
});

test("a landing oferece criar conta sem exigir login", async () => {
  await withBrowser(async (driver) => {
    await driver.get(baseUrl);
    await driver.findElement(By.linkText("Começar agora")).click();
    await driver.wait(until.urlContains("/cadastro"), 10000);
  }, null);
});
