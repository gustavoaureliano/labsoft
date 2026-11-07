import assert from "node:assert/strict";
import { afterEach, test } from "node:test";

process.env.NEXT_PUBLIC_AUTH_ENABLED = "true";
const api = await import("../src/lib/apiClient.ts");
const originalFetch = globalThis.fetch;
const originalNavigator = Object.getOwnPropertyDescriptor(globalThis, "navigator");
Object.defineProperty(globalThis, "navigator", {configurable: true, value: {locks: {request: async (_: string, action: () => Promise<unknown>) => action()}}});
afterEach(() => { globalThis.fetch = originalFetch; api.clearApiSession(); });
process.on("exit", () => { if (originalNavigator) Object.defineProperty(globalThis, "navigator", originalNavigator); });

test("FormData preserves browser multipart headers and handles 204", async () => {
  const body = new FormData(); body.append("file", new Blob(["video"]), "video.mp4");
  globalThis.fetch = async (url, init) => {
    assert.equal(url, "/api/media");
    assert.equal(init?.body, body);
    assert.equal(new Headers(init?.headers).has("Content-Type"), false);
    assert.equal(new Headers(init?.headers).has("Authorization"), false);
    assert.equal(init?.credentials, "same-origin");
    return new Response(null, {status: 204});
  };
  assert.equal(await api.request("/api/media", {method: "POST", body}), undefined);
});

test("structured catalog errors keep their message", async () => {
  globalThis.fetch = async () => Response.json({detail: {code: "invalid", message: "Curso possui pendências"}}, {status: 422});
  await assert.rejects(api.request("/api/courses"), /Curso possui pendências/);
});

test("expired upload is not renewed or replayed automatically", async () => {
  let calls = 0;
  globalThis.fetch = async () => { calls++; return Response.json({detail: "expired"}, {status: 401}); };
  await assert.rejects(api.request("/api/media", {method: "POST", body: new FormData()}), /operação não foi repetida/);
  assert.equal(calls, 1);
});

test("protected read renews once then retries with cookie", async () => {
  const calls: string[] = [];
  globalThis.fetch = async url => {
    calls.push(String(url));
    if (calls.length <= 2) return Response.json({detail: "expired"}, {status: 401});
    return Response.json({ok: true});
  };
  assert.deepEqual(await api.request("/api/learning/courses"), {ok: true});
  assert.deepEqual(calls, ["/api/learning/courses", "/api/v1/auth/me", "/api/v1/auth/refresh", "/api/learning/courses"]);
});

test("renewal rechecks cookies updated by another tab", async () => {
  const calls: string[] = [];
  globalThis.fetch = async url => { calls.push(String(url)); return Response.json({id: "real"}); };
  await Promise.all([api.renewApiSession(), api.renewApiSession()]);
  assert.deepEqual(calls, ["/api/v1/auth/me"]);
});

test("identity outage remains 503 without another refresh or request", async () => {
  const calls: string[] = [];
  globalThis.fetch = async url => {
    calls.push(String(url));
    return Response.json({detail: "Indisponível"}, {status: calls.length === 1 ? 401 : 503});
  };
  await assert.rejects(api.request("/api/learning/courses"), (e: unknown) => e instanceof api.ApiError && e.status === 503);
  assert.deepEqual(calls, ["/api/learning/courses", "/api/v1/auth/me"]);
});

test("explicit Bearer failure does not switch to cookie refresh", async () => {
  let calls = 0;
  globalThis.fetch = async (_url, init) => {
    calls++; assert.equal(new Headers(init?.headers).get("Authorization"), "Bearer invalid");
    return Response.json({detail: "invalid"}, {status: 401});
  };
  await assert.rejects(api.request("/api/learning/courses", {headers: {Authorization: "Bearer invalid"}}), (e: unknown) => e instanceof api.ApiError && e.status === 401);
  assert.equal(calls, 1);
});

test("public certificate verification never tries to renew", async () => {
  let calls = 0;
  globalThis.fetch = async () => { calls++; return Response.json({detail: "invalid"}, {status: 401}); };
  await assert.rejects(api.request("/api/learning/certificates/verify/example"));
  assert.equal(calls, 1);
});

test("failed logout does not broadcast successful termination", async () => {
  globalThis.fetch = async () => Response.json({id: "real", role: "student"});
  await api.getCurrentUserFromApi();
  assert.equal(api.hasApiSession(), true);
  globalThis.fetch = async () => Response.json({detail: "Unavailable"}, {status: 503});
  await assert.rejects(api.logoutFromApi());
  assert.equal(api.hasApiSession(), true);
});

test("session notifications ignore this tab and deduplicate other-tab events", () => {
  const windowDescriptor = Object.getOwnPropertyDescriptor(globalThis, "window");
  const storageDescriptor = Object.getOwnPropertyDescriptor(globalThis, "localStorage");
  const originalChannel = globalThis.BroadcastChannel;
  const channels: FakeChannel[] = [];
  class FakeChannel {
    onmessage: ((event: MessageEvent) => void) | null = null;
    constructor() { channels.push(this); }
    postMessage(data: unknown) { for (const c of channels) if (c !== this) c.onmessage?.(new MessageEvent("message", {data})); }
    close() { channels.splice(channels.indexOf(this), 1); }
  }
  Object.defineProperty(globalThis, "window", {configurable: true, value: new EventTarget()});
  Object.defineProperty(globalThis, "localStorage", {configurable: true, value: {setItem() {}}});
  globalThis.BroadcastChannel = FakeChannel as unknown as typeof BroadcastChannel;
  try {
    const events: string[] = [];
    const unsubscribe = api.subscribeSessionChanges(type => events.push(type));
    api.announceSessionChange("login");
    assert.deepEqual(events, []);
    const other = new FakeChannel();
    other.postMessage({type: "logout", id: "event-1", sender: "other-tab"});
    other.postMessage({type: "logout", id: "event-1", sender: "other-tab"});
    assert.deepEqual(events, ["logout"]);
    unsubscribe(); other.close();
  } finally {
    globalThis.BroadcastChannel = originalChannel;
    if (windowDescriptor) Object.defineProperty(globalThis, "window", windowDescriptor);
    else Reflect.deleteProperty(globalThis, "window");
    if (storageDescriptor) Object.defineProperty(globalThis, "localStorage", storageDescriptor);
    else Reflect.deleteProperty(globalThis, "localStorage");
  }
});
