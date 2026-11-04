import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { baseUrl } from "./browser.ts";

test("o proxy envia vídeo maior que 10 MiB sem truncar o multipart", {skip: process.env.E2E_BACKEND !== "true"}, async () => {
  assert.ok(process.env.E2E_VIDEO_PATH);
  const original = await readFile(process.env.E2E_VIDEO_PATH);
  const padded = Buffer.concat([original, Buffer.alloc(11 * 1024 * 1024)]);
  const form = new FormData();
  form.set("file", new Blob([padded], {type: "video/mp4"}), "large-test.mp4");
  const response = await fetch(`${baseUrl}/api/media`, {method: "POST", headers: {"X-Demo-User": "professor-demo"}, body: form});
  assert.equal(response.status, 201, await response.clone().text());
  const media = await response.json();
  assert.equal(media.size_bytes, padded.length);
  assert.ok(media.duration_seconds > 0);
});
