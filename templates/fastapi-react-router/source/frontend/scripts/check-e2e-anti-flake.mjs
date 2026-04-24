import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const ROOT = new URL("../tests/e2e/", import.meta.url);
const offenders = [];

function walk(directory) {
  for (const name of readdirSync(directory)) {
    const absolute = join(directory, name);
    const stat = statSync(absolute);
    if (stat.isDirectory()) {
      walk(absolute);
      continue;
    }
    if (!absolute.endsWith(".ts")) {
      continue;
    }
    const contents = readFileSync(absolute, "utf8");
    if (/\bwaitForTimeout\s*\(/.test(contents)) {
      offenders.push(absolute);
    }
  }
}

walk(ROOT.pathname);

if (offenders.length > 0) {
  console.error("Found forbidden waitForTimeout() usage in committed E2E specs:");
  for (const offender of offenders) {
    console.error(`- ${offender}`);
  }
  process.exit(1);
}
