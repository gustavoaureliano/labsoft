import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("curso e videoaula levam aos materiais demonstrativos do curso", {skip: process.env.E2E_BACKEND !== "true"}, async () => {
  const response = await fetch(`${baseUrl}/api/learning/courses/fisica-quantica`, {headers: {"X-Demo-User": "aluno-demo"}});
  assert.equal(response.status, 200);
  const course = await response.json();
  assert.ok(course.lessons.length > 0);
  await withBrowser(async driver => {
    await driver.get(`${baseUrl}/meus-cursos/fisica-quantica`);
    const section = await driver.wait(until.elementLocated(By.css('section[aria-labelledby="course-materials-title"]')), 10000);
    assert.equal((await section.findElements(By.css("li"))).length, 2);
    assert.match(await section.getText(), /sem arquivos disponíveis para download/i);
    const link = await section.findElement(By.linkText("Ver todos os materiais deste curso →"));
    await driver.executeScript("arguments[0].scrollIntoView({behavior:'instant',block:'center'})", link);
    await link.click();
    await driver.wait(until.urlContains("curso=fisica-quantica"), 10000);
    assert.equal(await driver.findElement(By.css('select[name="course-filter"]')).getAttribute("value"), "fisica-quantica");
    assert.equal((await driver.findElements(By.css('section[aria-labelledby="course-fisica-quantica"] li'))).length, 2);
    assert.match(await driver.findElement(By.css("main")).getText(), /2 materiais/);

    await driver.get(`${baseUrl}/meus-cursos/fisica-enem-mecanica`);
    await driver.wait(until.elementLocated(By.xpath('//h1[contains(., "Mecânica")]')), 10000);
    assert.equal((await driver.findElements(By.css('section[aria-labelledby="course-materials-title"]'))).length, 0);
    await driver.get(`${baseUrl}/materiais-complementares?curso=fisica-enem-mecanica`);
    assert.equal(await driver.findElement(By.css('select[name="course-filter"]')).getAttribute("value"), "fisica-enem-mecanica");
    assert.match(await driver.findElement(By.css("main")).getText(), /Nenhum material corresponde/);

    await driver.get(`${baseUrl}/videoaula?aula=${encodeURIComponent(course.lessons[0].id)}`);
    const materialsTab = await driver.wait(until.elementLocated(By.xpath('//button[@role="tab" and normalize-space()="Materiais"]')), 10000);
    await driver.executeScript("arguments[0].scrollIntoView({behavior:'instant',block:'center'})", materialsTab);
    await materialsTab.click();
    const lessonLink = await driver.findElement(By.linkText("Ver materiais deste curso →"));
    assert.match(await lessonLink.getAttribute("href") ?? "", /curso=fisica-quantica/);
    await driver.executeScript("arguments[0].scrollIntoView({behavior:'instant',block:'center'})", lessonLink);
    await lessonLink.click();
    await driver.wait(until.urlContains("curso=fisica-quantica"), 10000);

    await driver.manage().addCookie({name: "aprovaai_demo_user", value: "aluno-demo-2", path: "/"});
    await driver.get(`${baseUrl}/meus-cursos/fisica-quantica`);
    await driver.wait(until.elementLocated(By.css('[role="alert"]')), 10000);
    assert.equal((await driver.findElements(By.css('section[aria-labelledby="course-materials-title"]'))).length, 0);
  });
});
