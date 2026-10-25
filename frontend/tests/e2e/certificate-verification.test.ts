import assert from "node:assert/strict";
import { test } from "node:test";
import { By, until } from "selenium-webdriver";
import { baseUrl, setDemoRoleForTest, withBrowser } from "./browser.ts";

test("a verificação pública é legível, mas o PDF permanece privado", { skip: process.env.E2E_BACKEND !== "true" }, async () => {
  const response = await fetch(`${baseUrl}/api/learning/certificates`, { headers: { "X-Demo-User": "aluno-demo" } });
  assert.equal(response.status, 200);
  const certificates = await response.json();
  await withBrowser(async driver => {
    await driver.get(`${baseUrl}/certificados/verificar/codigo-inexistente`);
    await setDemoRoleForTest(driver, null);
    await driver.navigate().refresh();
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Certificado não encontrado"]')), 10000);
    assert.equal((await driver.findElements(By.css('a[href*="/download"]'))).length, 0);

    if (!certificates.length) return;
    const certificate = certificates[0];
    await driver.get(`${baseUrl}/certificados/verificar/${certificate.verification_code}`);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Registro de emissão encontrado"]')), 10000);
    const text = await driver.findElement(By.css("main")).getText();
    assert.ok(text.includes(certificate.course_title));
    assert.ok(text.includes(certificate.verification_code));
    assert.match(text, /não é uma assinatura digital qualificada/i);
    assert.equal((await driver.findElements(By.css('a[href*="/download"]'))).length, 0);

    await driver.get(`${baseUrl}/certificados/${certificate.id}`);
    await driver.wait(until.urlContains("/login"), 10000);
    const pdfStatus = await driver.executeAsyncScript<number>(
      "const id=arguments[0], done=arguments[arguments.length-1]; fetch('/api/learning/certificates/'+id+'/download').then(r=>done(r.status))",
      certificate.id,
    );
    assert.equal(pdfStatus, 401);
  }, null);
});

test("o proprietário vê os dados do certificado e o link de verificação amigável", { skip: process.env.E2E_BACKEND !== "true" }, async () => {
  const response = await fetch(`${baseUrl}/api/learning/certificates`, { headers: { "X-Demo-User": "aluno-demo" } });
  assert.equal(response.status, 200);
  const certificates = await response.json();
  if (!certificates.length) return;
  const certificate = certificates[0];
  await withBrowser(async driver => {
    await driver.get(`${baseUrl}/certificados/${certificate.id}`);
    await driver.wait(until.elementLocated(By.xpath('//h1[normalize-space()="Certificado de conclusão"]')), 10000);
    const text = await driver.findElement(By.css("main")).getText();
    assert.match(text, /Duração dos vídeos na emissão/);
    assert.ok(text.includes(certificate.verification_code));
    const verification = await driver.findElement(By.linkText("Verificar certificado"));
    assert.match(await verification.getAttribute("href") ?? "", /\/certificados\/verificar\//);
    assert.ok(await driver.findElement(By.linkText("Baixar PDF")).isDisplayed());
  });
});
