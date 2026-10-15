/**
 * Node module-resolution hook for the built-in test runner.
 *
 * Vite (dev/build) and TypeScript resolve extensionless relative imports
 * (`import { x } from './config'`). Node's ESM loader does not, so importing a
 * service module in a `node --test` file would fail with "Cannot find module".
 * This hook retries a failing relative specifier with a `.ts` extension so the
 * test runner can load the same modules Vite loads.
 *
 * Loaded via tests/register-hooks.mjs (see package.json "test").
 */
export async function resolve(specifier, context, nextResolve) {
  try {
    return await nextResolve(specifier, context);
  } catch (err) {
    if (specifier.startsWith('.') && !/\.[a-z]+$/i.test(specifier)) {
      return nextResolve(specifier + '.ts', context);
    }
    throw err;
  }
}
