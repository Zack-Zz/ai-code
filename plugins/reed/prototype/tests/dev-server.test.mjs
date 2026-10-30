import assert from "node:assert/strict";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { createServer } from "vite";

test("the prototype dev server binds only to IPv4 loopback by default", async () => {
  const server = await createServer({
    root: fileURLToPath(new URL("..", import.meta.url)),
    configFile: fileURLToPath(new URL("../vite.config.mjs", import.meta.url)),
    logLevel: "silent",
    server: { port: 0, strictPort: false, preTransformRequests: false, warmup: { clientFiles: [] } },
    optimizeDeps: { noDiscovery: true, include: [] },
  });
  try {
    await server.listen();
    const address = server.httpServer.address();
    assert.equal(address.address, "127.0.0.1");
    const response = await fetch(`http://127.0.0.1:${address.port}/`);
    assert.equal(response.status, 200);
    assert.match(await response.text(), /<div id="root"><\/div>/);
  } finally {
    await server.close();
  }
});
