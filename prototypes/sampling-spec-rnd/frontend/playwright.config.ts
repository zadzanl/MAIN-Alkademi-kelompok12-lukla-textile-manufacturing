import { defineConfig, devices } from '@playwright/test';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const frontendDirectory = dirname(fileURLToPath(import.meta.url));
const backendDirectory = resolve(frontendDirectory, '../backend');

export default defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.ts',
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: Boolean(process.env.CI),
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
  ],
  use: {
    baseURL: 'http://127.0.0.1:3009',
    headless: true,
    viewport: { width: 1280, height: 720 },
    screenshot: 'only-on-failure',
    trace: 'off',
    video: 'off',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 720 } },
    },
  ],
  webServer: [
    {
      name: 'backend',
      command: 'python -m uvicorn src.main:app --host 127.0.0.1 --port 8009',
      cwd: backendDirectory,
      url: 'http://127.0.0.1:8009/api/sampling-spec-rnd/health',
      timeout: 60_000,
      reuseExistingServer: false,
    },
    {
      name: 'frontend',
      command: 'npm run dev -- --host 127.0.0.1 --port 3009',
      cwd: frontendDirectory,
      env: { NODE_OPTIONS: '--dns-result-order=ipv4first', VITE_API_URL: '/api/sampling-spec-rnd' },
      url: 'http://127.0.0.1:3009',
      timeout: 60_000,
      reuseExistingServer: false,
    },
  ],
});