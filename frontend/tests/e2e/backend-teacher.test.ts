import assert from "node:assert/strict";
import { mkdtemp, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { By, Key, until, type WebDriver } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

async function click(driver: WebDriver, locator: By) {
  const element = await driver.wait(until.elementLocated(locator), 10000);
  await driver.executeScript("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'})", element);
  await element.click();
}

test("o professor edita uma aula sem perder texto durante upload, prévia e ordenação", { skip: process.env.E2E_BACKEND !== "true" }, async () => {
  assert.ok(process.env.E2E_VIDEO_PATH, "Set E2E_VIDEO_PATH to the generated test MP4");
  const directory = await mkdtemp(join(tmpdir(), "aprovaai-teacher-test-"));
  const invalidVideo = join(directory, "invalid.mp4");
  await writeFile(invalidVideo, "not a video");
  try {
  await withBrowser(async driver => {
    const listUrl = `${baseUrl}/professor/cursos/fisica-quantica/aulas`;
    let lessonId: string | undefined;
    try {
      await driver.get(listUrl);
      const add = await driver.wait(until.elementLocated(By.xpath("//button[normalize-space()='+ Adicionar aula']")), 10000);
      const count = (await driver.findElements(By.css('ol[aria-label="Aulas do curso"] > li'))).length;
      assert.equal((await driver.findElements(By.css('input[type="file"], video'))).length, 0, "A list must not render every editor/player");
      await add.click();
      await driver.wait(until.urlContains("/editar"), 10000);
      lessonId = decodeURIComponent(new URL(await driver.getCurrentUrl()).pathname.split("/").at(-2)!);
      await click(driver, By.xpath("//nav[@aria-label='Modo do editor']//button[normalize-space()='Prévia']"));
      await driver.wait(until.elementLocated(By.xpath("//h2[normalize-space()='Adicione um vídeo para visualizar a aula']")), 10000);
      await click(driver, By.xpath("//nav[@aria-label='Modo do editor']//button[normalize-space()='Editar']"));
      const title = `Aula Selenium ${Date.now()}`;
      const titleField = await driver.wait(until.elementLocated(By.css('input[name="lesson-title"]')), 10000);
      await titleField.sendKeys(Key.CONTROL, "a", Key.NULL, title);
      await driver.findElement(By.css('textarea[name="lesson-description"]')).sendKeys("Descrição ainda não salva durante o envio.");
      await driver.findElement(By.css('input[aria-label="Enviar vídeo"]')).sendKeys(invalidVideo);
      await driver.wait(until.elementLocated(By.css('[role="alert"]')), 10000);
      assert.equal(await titleField.getAttribute("value"), title, "Failed upload must also preserve drafts");
      await driver.findElement(By.css('input[aria-label="Enviar vídeo"]')).sendKeys(process.env.E2E_VIDEO_PATH!);
      await driver.wait(until.elementLocated(By.xpath("//*[@role='status' and normalize-space()='Vídeo atualizado.']")), 15000);
      assert.equal(await titleField.getAttribute("value"), title, "Upload must preserve the title draft and mounted input");
      assert.equal(await driver.findElement(By.css('textarea[name="lesson-description"]')).getAttribute("value"), "Descrição ainda não salva durante o envio.");
      if (process.env.E2E_THUMBNAIL_PATH) {
        await driver.findElement(By.css('input[aria-label="Trocar imagem"]')).sendKeys(process.env.E2E_THUMBNAIL_PATH);
        await driver.wait(until.elementLocated(By.xpath("//*[@role='status' and normalize-space()='Imagem atualizada.']")), 10000);
        assert.equal(await titleField.getAttribute("value"), title);
      }
      await click(driver, By.xpath("//nav[@aria-label='Modo do editor']//button[normalize-space()='Prévia']"));
      const video = await driver.wait(until.elementLocated(By.css("video")), 10000);
      await driver.wait(async () => driver.executeScript<boolean>("return arguments[0].readyState >= 1", video), 10000);
      assert.equal((await driver.findElements(By.css("video"))).length, 1);
      assert.equal((await driver.findElements(By.css('input[name="lesson-title"]'))).length, 0);
      assert.equal(await driver.findElement(By.css('section[aria-label="Prévia da aula"] h2')).getText(), title);
      const videoUrl = await video.getAttribute("src");
      await click(driver, By.xpath("//nav[@aria-label='Modo do editor']//button[normalize-space()='Editar']"));
      assert.equal((await driver.findElements(By.css("video"))).length, 0, "Leaving preview must unmount the video");
      assert.equal(await driver.findElement(By.css('input[name="lesson-title"]')).getAttribute("value"), title);
      await click(driver, By.xpath("//button[normalize-space()='Salvar informações']"));
      await driver.wait(until.elementLocated(By.xpath("//*[@role='status' and normalize-space()='Informações da aula salvas.']")), 10000);
      await driver.navigate().refresh();
      const saved = await driver.wait(until.elementLocated(By.css('input[name="lesson-title"]')), 10000);
      assert.equal(await saved.getAttribute("value"), title);
      await click(driver, By.linkText("← Voltar às aulas"));
      await driver.wait(until.elementLocated(By.css(`li[data-lesson-id="${lessonId}"]`)), 10000);
      assert.equal((await driver.findElements(By.css('ol[aria-label="Aulas do curso"] > li'))).length, count + 1);
      await click(driver, By.css(`li[data-lesson-id="${lessonId}"] button[title="Mover para cima"]`));
      await driver.wait(until.elementLocated(By.xpath("//*[@role='status' and normalize-space()='Ordem das aulas salva.']")), 10000);
      const rows = await driver.findElements(By.css('ol[aria-label="Aulas do curso"] > li'));
      assert.equal(await rows[count - 1].getAttribute("data-lesson-id"), lessonId);
      await click(driver, By.xpath(`//li[@data-lesson-id="${lessonId}"]//a[normalize-space()='Editar aula']`));
      await click(driver, By.xpath("//button[normalize-space()='Excluir aula']"));
      await driver.switchTo().alert().accept();
      await driver.wait(until.urlIs(listUrl), 10000);
      await driver.wait(async () => (await driver.findElements(By.css('ol[aria-label="Aulas do curso"] > li'))).length === count, 10000);
      lessonId = undefined;
      const status = await driver.executeAsyncScript<number>("const url = arguments[0], done = arguments[arguments.length - 1]; fetch(url, {headers: {Range: 'bytes=0-15'}}).then(r => done(r.status));", videoUrl);
      assert.equal(status, 206, "Deleting the lesson must preserve its owner's video");
    } finally {
      if (lessonId) await driver.executeAsyncScript("const id = arguments[0], done = arguments[arguments.length-1]; fetch('/api/learning/lessons/' + id, {method:'DELETE'}).then(() => done()).catch(() => done());", lessonId);
    }
  }, "teacher");
  } finally { await rm(directory, {recursive: true, force: true}); }
});

test("as rotas de aulas respeitam o curso e o layout móvel", {skip: process.env.E2E_BACKEND !== "true"}, async () => {
  await withBrowser(async driver => {
    await driver.manage().window().setRect({width: 390, height: 844});
    await driver.get(`${baseUrl}/professor/cursos/fisica-quantica/aulas`);
    await driver.wait(until.elementLocated(By.css('ol[aria-label="Aulas do curso"]')), 10000);
    assert.equal(await driver.executeScript("return document.documentElement.scrollWidth <= innerWidth"), true);
    await driver.get(`${baseUrl}/professor/cursos/fisica-quantica/aulas/demo-quantica-introducao/editar?modo=previa`);
    await driver.wait(until.elementLocated(By.css("video")), 10000);
    assert.equal(await driver.executeScript("return document.documentElement.scrollWidth <= innerWidth"), true);
    await click(driver, By.xpath("//nav[@aria-label='Modo do editor']//button[normalize-space()='Editar']"));
    assert.equal((await driver.findElements(By.css("video"))).length, 0);
    await driver.get(`${baseUrl}/professor/cursos/fisica-enem-mecanica/aulas/demo-quantica-introducao/editar`);
    await driver.wait(until.elementLocated(By.xpath("//h1[normalize-space()='Aula não encontrada neste curso']")), 10000);
    assert.equal((await driver.findElements(By.css('input[name="lesson-title"]'))).length, 0);
    await driver.get(`${baseUrl}/professor/cursos/biologia-celular/aulas`);
    await driver.wait(until.elementLocated(By.css('[role="alert"]')), 10000);
    assert.equal((await driver.findElements(By.xpath("//button[normalize-space()='+ Adicionar aula']"))).length, 0);
  }, "teacher");
});
