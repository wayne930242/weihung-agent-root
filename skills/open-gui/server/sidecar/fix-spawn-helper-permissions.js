"use strict";

// node-pty's `spawn-helper` binary loses its executable bit on extraction on this
// machine, under both `npm install` and `deno install` — confirmed via smoke test
// (see ../../../../openspec/changes/grill-with-web/design.md, D3). This is not
// specific to how node-pty builds; it's a packaging/extraction quirk, so we assert
// the bit defensively rather than trust the installer.

const fs = require("fs");
const path = require("path");

const roots = [
  path.join(__dirname, "node_modules", "node-pty", "build", "Release", "spawn-helper"),
  path.join(__dirname, "node_modules", "node-pty", "build", "Debug", "spawn-helper"),
  path.join(__dirname, "node_modules", "node-pty", "prebuilds", "darwin-arm64", "spawn-helper"),
  path.join(__dirname, "node_modules", "node-pty", "prebuilds", "darwin-x64", "spawn-helper"),
];

for (const helperPath of roots) {
  if (fs.existsSync(helperPath)) {
    fs.chmodSync(helperPath, 0o755);
    console.log(`[open-gui-sidecar] chmod +x ${helperPath}`);
  }
}
