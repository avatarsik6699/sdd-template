import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const e2eDir = path.join(root, 'tests', 'e2e');
const forbiddenPattern = /\bwaitForTimeout\s*\(/;
const allowMarker = 'e2e-debug-allow-wait';

function walk(dir) {
  const files = [];
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      files.push(...walk(full));
      continue;
    }
    if (full.endsWith('.ts')) {
      files.push(full);
    }
  }
  return files;
}

if (!existsSync(e2eDir)) {
  console.error('E2E directory not found:', e2eDir);
  process.exit(1);
}

const violations = [];
for (const file of walk(e2eDir)) {
  const text = readFileSync(file, 'utf8');
  const lines = text.split(/\r?\n/);

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    if (!forbiddenPattern.test(line)) {
      continue;
    }

    const sameLineAllowed = line.includes(allowMarker);
    const previousLineAllowed = i > 0 && lines[i - 1].includes(allowMarker);
    if (sameLineAllowed || previousLineAllowed) {
      continue;
    }

    violations.push(`${path.relative(root, file)}:${i + 1}`);
  }
}

if (violations.length > 0) {
  console.error(
    'Anti-flake check failed: `waitForTimeout(...)` is forbidden in committed E2E tests.'
  );
  console.error('Use web-first assertions (`await expect(...)`) instead.');
  console.error('Violations:');
  for (const item of violations) {
    console.error(`  - ${item}`);
  }
  console.error(
    'If you need a temporary local debug pause, annotate with `// e2e-debug-allow-wait` and do not commit it.'
  );
  process.exit(1);
}

console.log('Anti-flake check passed: no forbidden `waitForTimeout(...)` usage found.');
