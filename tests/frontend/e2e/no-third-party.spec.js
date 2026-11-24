import { expect, test } from "@playwright/test";

// The site must make no requests to third-party servers: every font, script,
// wasm file and runtime file is self-hosted (see README.md, "Self-hosted
// dependencies"). This test runs the real app, unmocked, with the real Ace
// editor and the real Pyodide worker, evaluates a dice program to completion
// and fails if any request (page, worker, font, fetch, ...) leaves the local
// test server.
//
// Requests are observed at the browser-context level so that requests made
// by the web worker (importScripts, fetch of the wasm and stdlib) are seen
// too. Foreign requests are aborted rather than let through, so the test
// itself never contacts a third party either.

const LOCAL_ORIGIN = new URL("http://127.0.0.1:4173").origin;

function isLocal(url) {
  // data: and blob: URLs never leave the browser.
  if (url.startsWith("data:") || url.startsWith("blob:")) {
    return true;
  }
  return new URL(url).origin === LOCAL_ORIGIN;
}

test("runs a dice program without requesting any third-party host", async ({ context, page }) => {
  // Booting Pyodide and evaluating takes a few seconds; leave headroom.
  test.setTimeout(120_000);

  const foreignRequests = [];
  await context.route("**/*", async (route) => {
    const url = route.request().url();
    if (isLocal(url)) {
      await route.continue();
      return;
    }
    foreignRequests.push(url);
    await route.abort("blockedbyclient");
  });
  // context.route does not see every worker request in every browser
  // version, so also listen to all requests the context reports.
  context.on("request", (request) => {
    const url = request.url();
    if (!isLocal(url) && !foreignRequests.includes(url)) {
      foreignRequests.push(url);
    }
  });

  await page.goto("/");
  await page.locator("#run-button").click();

  // Wait until the program has run to completion, or stop early as soon as a
  // foreign request shows up: a blocked CDN load would otherwise only surface
  // as a timeout, and the assertion below names the offending URL instead.
  const textOutput = page.locator("#text-output");
  await expect
    .poll(async () => foreignRequests.length > 0 || (await textOutput.textContent()).trim() !== "", {
      timeout: 90_000,
    })
    .toBe(true);
  expect(foreignRequests).toEqual([]);

  // The worker booted Pyodide and evaluated the program without a diagnostic,
  // and the real Ace editor is in use (not the textarea fallback).
  await expect(textOutput).not.toHaveText("");
  await expect(page.locator("#diagnostic-panel")).toBeHidden();
  await expect(page.locator("#editor.ace_editor")).toBeVisible();
});
