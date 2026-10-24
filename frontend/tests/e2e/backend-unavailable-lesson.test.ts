import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("aula sem vídeo mantém contexto, mas não o expõe a aluno sem acesso", { skip: process.env.E2E_BACKEND !== "true" }, async () => {
  const courseId = "fisica-quantica";
  const headers = { "X-Demo-User": "professor-demo" };
  const courseResponse = await fetch(`${baseUrl}/api/learning/courses/${courseId}`, { headers });
  assert.equal(courseResponse.status, 200);
  const course = await courseResponse.json();
  const title = "Aula indisponível de teste";
  const description = "Descrição que continua visível mesmo sem vídeo.";
  const created = await fetch(`${baseUrl}/api/learning/lessons`, {
    method: "POST",
    headers: { ...headers, "Content-Type": "application/json" },
    body: JSON.stringify({
      course_id: courseId,
      title,
      description,
      position: Math.max(0, ...course.lessons.map((lesson: { position: number }) => lesson.position)) + 1,
    }),
  });
  assert.equal(created.status, 201);
  const lesson = await created.json();

  try {
    await withBrowser(async (driver) => {
      await driver.get(`${baseUrl}/videoaula?aula=${lesson.id}`);
      await driver.wait(until.elementLocated(By.xpath(`//h1[normalize-space()="${title}"]`)), 10000);
      assert.match(await driver.findElement(By.css("main")).getText(), /Descrição que continua visível/);
      assert.ok(await driver.findElement(By.css('section[aria-label="Videoaula"] [role="alert"]')).isDisplayed());
      assert.equal((await driver.findElements(By.css("video"))).length, 0);
      assert.ok(await driver.findElement(By.linkText("← Aula anterior")).isDisplayed());
      assert.ok(await driver.findElement(By.linkText("← Voltar para o curso")).isDisplayed());

      await driver.manage().addCookie({ name: "aprovaai_demo_user", value: "aluno-demo-2", path: "/" });
      await driver.navigate().refresh();
      await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Aula indisponível"]')), 10000);
      assert.equal((await driver.findElements(By.xpath(`//h1[normalize-space()="${title}"]`))).length, 0);
      assert.equal((await driver.findElements(By.css("video"))).length, 0);
    });
  } finally {
    const removed = await fetch(`${baseUrl}/api/learning/lessons/${lesson.id}`, { method: "DELETE", headers });
    assert.equal(removed.status, 204);
  }
});
