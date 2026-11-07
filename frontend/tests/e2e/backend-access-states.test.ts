import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("Meus Cursos distingue acesso ativo, expirado e bloqueado sem abrir aulas protegidas", { skip: process.env.E2E_BACKEND !== "true" }, async () => {
  await withBrowser(async (driver) => {
    await driver.manage().addCookie({ name: "aprovaai_demo_user", value: "aluno-acesso-demo", path: "/" });
    await driver.get(`${baseUrl}/meus-cursos`);
    await driver.wait(async () => (await driver.findElements(By.css('section[aria-labelledby="in-progress-title"] article'))).length === 3, 10000);
    const courseSection = await driver.findElement(By.css('section[aria-labelledby="in-progress-title"]'));
    assert.match(await courseSection.getText(), /Começar curso|Continuar curso/);
    assert.match(await courseSection.getText(), /Acesso expirado/);
    assert.match(await courseSection.getText(), /Acesso bloqueado/);
    for (const [title, state] of [["Introdução à Física Quântica", "expired"], ["Biologia Celular", "blocked"]]) {
      const card = await courseSection.findElement(By.xpath(`.//article[.//h3[contains(normalize-space(), "${title}")]]`));
      assert.equal(await card.findElement(By.css("[data-state]")).getAttribute("data-state"), state);
      assert.match(await card.findElement(By.css("a")).getAttribute("href") ?? "", /\/cursos\//);
      assert.equal((await card.findElements(By.xpath('.//*[contains(text(), "Progresso do curso")]'))).length, 0);
    }
    const response = await driver.executeAsyncScript<number>(
      "const done=arguments[arguments.length-1]; fetch('/api/learning/lessons/demo-quantica-introducao/playback').then(r=>done(r.status))",
    );
    assert.equal(response, 403);
    await driver.get(`${baseUrl}/videoaula?aula=demo-quantica-introducao`);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Aula indisponível"]')), 10000);
    assert.equal((await driver.findElements(By.css("video"))).length, 0);
    await driver.get(`${baseUrl}/cursos/fisica-quantica`);
    assert.ok(await driver.wait(until.elementLocated(By.xpath('//*[normalize-space()="Acesso expirado"]')), 10000));
    assert.equal((await driver.findElements(By.linkText("Continuar curso"))).length, 0);
  });
});
