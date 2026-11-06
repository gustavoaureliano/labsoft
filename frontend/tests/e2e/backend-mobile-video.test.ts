import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, withBrowser } from "./browser.ts";

test("videoaula ocupa a largura móvel sem cortar o vídeo ou criar rolagem horizontal", {skip: process.env.E2E_BACKEND !== "true"}, async () => {
  const response = await fetch(`${baseUrl}/api/learning/courses/fisica-quantica`, {headers: {"X-Demo-User": "aluno-demo"}});
  assert.equal(response.status, 200);
  const course = await response.json();
  const lesson = course.lessons.find((item: {id: string; playable: boolean}) => item.playable);
  assert.ok(lesson, "O curso de demonstração precisa ter uma aula reproduzível");

  await withBrowser(async driver => {
    await driver.get(`${baseUrl}/videoaula?aula=${encodeURIComponent(lesson.id)}`);
    const video = await driver.wait(until.elementLocated(By.css('section[aria-label="Videoaula"] video')), 10000);
    for (const [width, height] of [[320, 568], [375, 667], [390, 844], [390, 400], [600, 420], [667, 375], [844, 390], [844, 520], [900, 600]]) {
      await driver.manage().window().setRect({width, height});
      const geometry = await driver.executeScript<{
        left: number; right: number; width: number; height: number; viewport: number;
        viewportHeight: number; scrollWidth: number; fit: string; controls: boolean; headerPosition: string;
      }>(`const video=arguments[0], rect=video.getBoundingClientRect(); return {
        left:rect.left, right:rect.right, width:rect.width, height:rect.height,
        viewport:document.documentElement.clientWidth, viewportHeight:innerHeight,
        scrollWidth:document.documentElement.scrollWidth, fit:getComputedStyle(video).objectFit,
        controls:video.controls, headerPosition:getComputedStyle(document.querySelector('header')).position
      }`, video);
      assert.ok(Math.abs(geometry.left) <= 1);
      assert.ok(Math.abs(geometry.right - geometry.viewport) <= 1);
      assert.ok(geometry.scrollWidth <= geometry.viewport);
      assert.equal(geometry.fit, "contain");
      assert.equal(geometry.controls, true);
      if (geometry.viewportHeight <= 600 && width / geometry.viewportHeight >= 4 / 5) {
        assert.equal(geometry.headerPosition, "static");
        assert.ok(geometry.height <= Math.max(160, geometry.viewportHeight - 24) + 1);
        await driver.executeScript("arguments[0].scrollIntoView({behavior:'instant',block:'center'})", video);
        const visible = await driver.executeScript<{top: number; bottom: number; viewportHeight: number}>(
          "const rect=arguments[0].getBoundingClientRect(); return {top:rect.top,bottom:rect.bottom,viewportHeight:innerHeight}", video,
        );
        assert.ok(visible.top >= -1 && visible.bottom <= visible.viewportHeight + 1, "O player inteiro precisa caber após a rolagem");
      } else {
        assert.equal(geometry.headerPosition, "sticky");
        assert.ok(Math.abs(geometry.height - geometry.width * 9 / 16) <= 1);
      }
    }

    await driver.manage().window().setRect({width: 375, height: 667});
    await driver.executeScript("arguments[0].dispatchEvent(new Event('error'))", video);
    const unavailable = await driver.wait(until.elementLocated(By.css('section[aria-label="Videoaula"] [role="alert"]')), 10000);
    const fallback = await driver.executeScript<{left: number; right: number; viewport: number; scrollWidth: number}>(
      "const rect=arguments[0].getBoundingClientRect(); return {left:rect.left,right:rect.right,viewport:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth}",
      unavailable,
    );
    assert.ok(Math.abs(fallback.left) <= 1);
    assert.ok(Math.abs(fallback.right - fallback.viewport) <= 1);
    assert.ok(fallback.scrollWidth <= fallback.viewport);
    assert.ok(await driver.findElement(By.linkText("Próxima aula →")).isDisplayed());

    await driver.manage().window().setRect({width: 768, height: 900});
    await driver.navigate().refresh();
    const tabletVideo = await driver.wait(until.elementLocated(By.css('section[aria-label="Videoaula"] video')), 10000);
    const tabletLeft = await driver.executeScript<number>("return arguments[0].getBoundingClientRect().left", tabletVideo);
    assert.ok(tabletLeft > 0, "Tablets mantêm as margens normais do conteúdo");

    await driver.manage().window().setRect({width: 667, height: 375});
    await driver.get(`${baseUrl}/meus-cursos`);
    const otherPageHeader = await driver.executeScript<string>("return getComputedStyle(document.querySelector('header')).position");
    assert.equal(otherPageHeader, "sticky", "Somente a videoaula libera o cabeçalho em telas baixas");
  });
});

test("a prévia do professor mantém as margens e a proporção do player", {skip: process.env.E2E_BACKEND !== "true"}, async () => {
  const response = await fetch(`${baseUrl}/api/learning/courses/fisica-quantica`, {headers: {"X-Demo-User": "professor-demo"}});
  assert.equal(response.status, 200);
  const course = await response.json();
  const lesson = course.lessons.find((item: {id: string; playable: boolean}) => item.playable);
  assert.ok(lesson);
  await withBrowser(async driver => {
    await driver.manage().window().setRect({width: 390, height: 844});
    await driver.get(`${baseUrl}/professor/cursos/fisica-quantica/aulas/${encodeURIComponent(lesson.id)}/editar?modo=previa`);
    const video = await driver.wait(until.elementLocated(By.css('section[aria-label="Prévia da aula"] video')), 10000);
    const dimensions = await driver.executeScript<{left: number; right: number; viewport: number; width: number; height: number}>(
      "const rect=arguments[0].getBoundingClientRect(); return {left:rect.left,right:rect.right,width:rect.width,height:rect.height,viewport:document.documentElement.clientWidth}", video,
    );
    assert.ok(dimensions.left > 0 && dimensions.right < dimensions.viewport);
    assert.ok(Math.abs(dimensions.height - dimensions.width * 9 / 16) <= 1);
  }, "teacher");
});
