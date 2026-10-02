import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o professor acompanha relatórios financeiros e de engajamento", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/professor/monetizacao`);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Monetização e desempenho"]')), 10000);
    await pauseForReview();

    const pageText = await driver.findElement(By.css("main")).getText();
    assert.match(pageText, /Receita mensal\s+R\$ 9\.240/);
    assert.match(pageText, /Saldo disponível\s+R\$ 7\.890/);
    assert.match(pageText, /Alunos pagantes\s+924/);

    const financialReport = await driver.findElement(By.xpath('//section[.//h2[normalize-space()="Evolução da receita"]]'));
    assert.match(await financialReport.getText(), /R\$ 44\.550/);
    assert.match(await financialReport.getText(), /Set/);

    const engagementReport = await driver.findElement(By.xpath('//section[.//h2[normalize-space()="Atividade dos alunos"]]'));
    assert.match(await engagementReport.getText(), /Taxa de conclusão\s+78,4%/);
    assert.match(await engagementReport.getText(), /Avaliação média\s+4,8\/5/);

    const courseRows = await driver.findElements(By.css("table tbody tr"));
    assert.equal(courseRows.length, 3);
    assert.match(await courseRows[0].getText(), /Introdução à Filosofia 486 R\$ 4\.860 52,6%/);
    await pauseForReview();
  }, "teacher");
});
