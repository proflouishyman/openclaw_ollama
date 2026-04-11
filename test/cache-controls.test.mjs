import assert from "node:assert/strict";
import test from "node:test";

import {
  injectOllamaCacheControls,
  mergeOllamaOptions,
  resolveOllamaReliabilityControls,
  resolveOllamaCacheControls,
  wrapStreamFnWithOllamaCacheControls,
} from "../lib/cache-controls.js";

test("resolveOllamaCacheControls reads keepAlive and options", () => {
  const controls = resolveOllamaCacheControls({
    ollama: {
      keepAlive: "15m",
      options: { num_batch: 8 },
    },
  });
  assert.deepEqual(controls, {
    keepAlive: "15m",
    options: { num_batch: 8 },
  });
});

test("injectOllamaCacheControls injects keep_alive when payload omits it", () => {
  const payload = { model: "gemma4:26b", options: { num_ctx: 32768 } };
  injectOllamaCacheControls(payload, { keepAlive: "1h", options: undefined });
  assert.equal(payload.keep_alive, "1h");
});

test("injectOllamaCacheControls preserves payload keep_alive when already present", () => {
  const payload = { model: "gemma4:26b", keep_alive: "2h" };
  injectOllamaCacheControls(payload, { keepAlive: "30m", options: undefined });
  assert.equal(payload.keep_alive, "2h");
});

test("mergeOllamaOptions keeps core-managed keys authoritative", () => {
  const merged = mergeOllamaOptions(
    { num_ctx: 32768, temperature: 0.1, num_predict: 512, top_k: 40 },
    { num_ctx: 1024, temperature: 0.9, num_predict: 32, num_batch: 16, top_k: 5 },
  );
  assert.equal(merged.num_ctx, 32768);
  assert.equal(merged.temperature, 0.1);
  assert.equal(merged.num_predict, 512);
  assert.equal(merged.num_batch, 16);
  assert.equal(merged.top_k, 5);
});

test("no params returns stream function unchanged", () => {
  const base = () => "ok";
  assert.strictEqual(wrapStreamFnWithOllamaCacheControls(base, undefined), base);
});

function createCollectorStream() {
  const events = [];
  let ended = false;
  let resolveEnded;
  const endedPromise = new Promise((resolve) => {
    resolveEnded = resolve;
  });
  return {
    push(event) {
      events.push(event);
    },
    end() {
      ended = true;
      resolveEnded();
    },
    get events() {
      return events;
    },
    get ended() {
      return ended;
    },
    endedPromise,
  };
}

async function* streamFromEvents(events) {
  for (const event of events) yield event;
}

test("resolveOllamaReliabilityControls reads reliability config", () => {
  const controls = resolveOllamaReliabilityControls({
    ollama: {
      reliability: {
        requestTimeoutMs: 90000,
        maxRetries: 2,
        retryBackoffMs: 150,
      },
    },
  });
  assert.deepEqual(controls, {
    requestTimeoutMs: 90000,
    maxRetries: 2,
    retryBackoffMs: 150,
  });
});

test("retries transient early stream errors and suppresses failed attempt events", async () => {
  let calls = 0;
  const base = () => {
    calls += 1;
    if (calls === 1) {
      return streamFromEvents([
        { type: "error", error: { errorMessage: "Ollama API stream ended without a final response" } },
      ]);
    }
    return streamFromEvents([
      { type: "start" },
      { type: "text_start" },
      { type: "text_delta", delta: "OK" },
      { type: "done" },
    ]);
  };

  const wrapped = wrapStreamFnWithOllamaCacheControls(
    base,
    { ollama: { reliability: { maxRetries: 1, retryBackoffMs: 0 } } },
    createCollectorStream,
  );
  const out = wrapped({}, {}, {});
  await out.endedPromise;

  assert.equal(calls, 2);
  assert.deepEqual(
    out.events.map((event) => event.type),
    ["start", "text_start", "text_delta", "done"],
  );
});

test("does not retry once stream has emitted material output", async () => {
  let calls = 0;
  const base = () => {
    calls += 1;
    return streamFromEvents([
      { type: "start" },
      { type: "text_start" },
      { type: "text_delta", delta: "partial" },
      { type: "error", error: { errorMessage: "Ollama API stream ended without a final response" } },
    ]);
  };

  const wrapped = wrapStreamFnWithOllamaCacheControls(
    base,
    { ollama: { reliability: { maxRetries: 2, retryBackoffMs: 0 } } },
    createCollectorStream,
  );
  const out = wrapped({}, {}, {});
  await out.endedPromise;

  assert.equal(calls, 1);
  assert.deepEqual(
    out.events.map((event) => event.type),
    ["start", "text_start", "text_delta", "error"],
  );
});
