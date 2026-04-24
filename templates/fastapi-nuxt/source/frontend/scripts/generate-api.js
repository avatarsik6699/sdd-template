import { execSync } from 'child_process';
import fs from 'fs';

const API_URL = process.env.API_URL || 'http://localhost:8000';
// Basic auth is optional for FastAPI by default, but kept here if your production/stage requires it
const LOGIN = process.env.API_LOGIN;
const PASSWORD = process.env.API_PASSWORD;

const SCHEMA_PATH = 'schema.json';
// FastAPI serves openapi.json at the root by default
const OPENAPI_ENDPOINT = '/openapi.json';
const OUTPUT_TYPES_PATH = 'app/types/schema.ts';

// Функция для санитизации сообщений логов
const sanitizeLogMessage = (message) => {
  if (typeof message !== 'string') {
    return String(message);
  }
  // Убираем переносы строк и другие управляющие символы
  return message.replace(/\r/g, '').replace(/\n/g, ' ').replace(/\t/g, ' ').trim();
};

const log = (message) => console.log(`[API Generator] ${sanitizeLogMessage(message)}`);
const error = (message) => console.error(`[API Generator] ❌ ${sanitizeLogMessage(message)}`);

const downloadSchema = async () => {
  log(`Downloading OpenAPI schema from ${API_URL}${OPENAPI_ENDPOINT}...`);

  const headers = {};
  if (LOGIN && PASSWORD) {
    const credentials = Buffer.from(`${LOGIN}:${PASSWORD}`).toString('base64');
    headers['Authorization'] = `Basic ${credentials}`;
  }

  try {
    const response = await fetch(`${API_URL}${OPENAPI_ENDPOINT}`, { headers });

    if (!response.ok) {
      throw new Error(`Failed to download schema: ${response.status} ${response.statusText}`);
    }

    const schema = await response.json();

    // Добавить валидацию структуры схемы
    if (!schema || typeof schema !== 'object') {
      throw new Error('Invalid OpenAPI schema structure');
    }

    // Санитизация пути файла
    const safePath = SCHEMA_PATH.replace(/[^a-zA-Z0-9._-]/g, '');

    fs.writeFileSync(safePath, JSON.stringify(schema, null, 2), {
      encoding: 'utf8',
      mode: 0o644, // Ограничение прав доступа
    });

    log('✓ Schema downloaded');
  } catch (err) {
    throw new Error(`Download error: ${err.message}`);
  }
};

const generateTypes = () => {
  log('Generating TypeScript types...');

  // Убедимся, что директория для типов существует
  const outputDir = OUTPUT_TYPES_PATH.substring(0, OUTPUT_TYPES_PATH.lastIndexOf('/'));
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  try {
    execSync(
      `npx openapi-typescript ${SCHEMA_PATH} -o ${OUTPUT_TYPES_PATH} && eslint ${OUTPUT_TYPES_PATH} --fix`,
      { stdio: 'inherit' }
    );
    log('✓ Types generated successfully');
  } catch (err) {
    throw new Error(`Type generation error: ${err.message}`);
  }
};

const cleanup = () => {
  if (fs.existsSync(SCHEMA_PATH)) {
    fs.unlinkSync(SCHEMA_PATH);
    log('✓ Cleanup completed');
  }
};

const main = async () => {
  try {
    log('Starting API generation process...\n');

    await downloadSchema();
    generateTypes();
    cleanup();

    log('\n🎉 API generation completed successfully!');
    process.exit(0);
  } catch (err) {
    error(err.message);
    cleanup();
    process.exit(1);
  }
};

main();
