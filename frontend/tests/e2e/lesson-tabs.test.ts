import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, pauseForReview, withBrowser } from "./browser.ts";

test("o aluno explora as abas da videoaula e persiste interações no banco", async () => {
  await withBrowser(async (driver) => {
    await driver.get(`${baseUrl}/videoaula`);
    await driver.executeScript("document.documentElement.style.scrollBehavior = 'auto'");
    const panel = await driver.wait(until.elementLocated(By.css('[role="tabpanel"]')), 10000);
    assert.match(await panel.getText(), /Sobre esta aula/);
    await pauseForReview();

    await driver.findElement(By.css('[role="tab"][id="tab-1"]')).click();
    assert.match(await panel.getText(), /Seja o primeiro a comentar/);
    await driver.findElement(By.id("lesson-comment")).sendKeys("Agora entendi a segunda lei!");
    await panel.findElement(By.css('button[type="submit"]')).click();
    await driver.wait(until.elementTextContains(panel, "Agora entendi a segunda lei!"), 5000);
    assert.match(await panel.getText(), /Agora entendi a segunda lei!/);
    await pauseForReview();

    await driver.findElement(By.css('[role="tab"][id="tab-2"]')).click();
    await driver.findElement(By.id("lesson-note")).sendKeys("Revisar força resultante.");
    await driver.findElement(By.xpath('//button[normalize-space()="Salvar anotação"]')).click();
    await driver.wait(until.elementTextContains(panel, "Anotação salva neste navegador"), 5000);
    assert.match(await panel.getText(), /Anotação salva neste navegador/);
    await pauseForReview();

    await driver.findElement(By.css('[role="tab"][id="tab-3"]')).click();
    await driver.findElement(By.css('button[aria-label="Avaliar com 5 estrelas"]')).click();
    await driver.wait(until.elementTextContains(panel, "Sua avaliação: 5 estrelas"), 5000);
    assert.match(await panel.getText(), /Sua avaliação: 5 estrelas/);
    await pauseForReview();

    // Reload page to confirm comment, note and rating were persisted in the database
    await driver.navigate().refresh();
    await driver.executeScript("document.documentElement.style.scrollBehavior = 'auto'");
    const reloadedPanel = await driver.wait(until.elementLocated(By.css('[role="tabpanel"]')), 10000);
    await driver.findElement(By.css('[role="tab"][id="tab-1"]')).click();
    await driver.wait(until.elementTextContains(reloadedPanel, "Agora entendi a segunda lei!"), 5000);

    // Simulate a backend error on comment creation and verify it does NOT appear in the UI list
    await driver.executeScript(`
      const origFetch = window.fetch;
      window.fetch = async (input, init) => {
        if (String(input).includes("/comments") && init?.method === "POST") {
          return new Response(JSON.stringify({ detail: "Falha simulada no banco de dados" }), {
            status: 500,
            headers: { "Content-Type": "application/json" },
          });
        }
        return origFetch(input, init);
      };
    `);
    await driver.findElement(By.id("lesson-comment")).sendKeys("Comentário que não deve persistir");
    const submitBtn = await reloadedPanel.findElement(By.css('button[type="submit"]'));
    await driver.executeScript("arguments[0].scrollIntoView({block: 'center'});", submitBtn);
    await submitBtn.click();
    await driver.wait(
      until.elementTextContains(reloadedPanel, "Erro ao publicar comentário: Falha simulada no banco de dados"),
      5000
    );
    const commentItems = await reloadedPanel.findElements(By.css("ul li"));
    assert.equal(commentItems.length, 1);
    assert.doesNotMatch(await commentItems[0].getText(), /Comentário que não deve persistir/);

    const tab4 = await driver.findElement(By.css('[role="tab"][id="tab-4"]'));
    await driver.executeScript("arguments[0].scrollIntoView({block: 'center'});", tab4);
    await tab4.click();
    const materialsLink = await driver.findElement(By.linkText("Explorar materiais →"));
    assert.match((await materialsLink.getAttribute("href")) ?? "", /materiais-complementares/);
    await pauseForReview();
  });
});
