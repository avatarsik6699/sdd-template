import { useCookie } from '#imports';
import type { CookieOptions } from 'nuxt/app';

export namespace SafeCookieTypes {
  export type KeyWithVersion = { key: string; version: string };
  export type DataWithVersion<T> = { version: string; data: T };
  export type WithMigration<T> = {
    migrate?: (oldData: unknown, oldVersion: string, newVersion: string) => T;
  };
}

const setItem = <T>(args: {
  keyWithVersion: SafeCookieTypes.KeyWithVersion;
  value: T;
  options?: CookieOptions<SafeCookieTypes.DataWithVersion<T>>;
}): void => {
  const { keyWithVersion, value, options } = args;

  const dataWithVersion: SafeCookieTypes.DataWithVersion<T> = {
    version: keyWithVersion.version,
    data: value,
  };

  try {
    const cookie = useCookie<SafeCookieTypes.DataWithVersion<T> | null>(
      keyWithVersion.key,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      options as any
    );
    cookie.value = dataWithVersion;
  } catch (error) {
    console.error(`[safeCookie]: Failed to save to cookie [${keyWithVersion.key}]:`, error);
  }
};

const getItem = <T>(args: {
  keyWithVersion: SafeCookieTypes.KeyWithVersion;
  migrationConfig?: SafeCookieTypes.WithMigration<T>;
}): T | undefined => {
  const { keyWithVersion, migrationConfig } = args;

  try {
    const cookie = useCookie<SafeCookieTypes.DataWithVersion<unknown> | null>(keyWithVersion.key);
    const raw = cookie.value;
    const parsed =
      typeof raw === 'string' ? (JSON.parse(raw) as SafeCookieTypes.DataWithVersion<unknown>) : raw;

    if (!parsed) {
      return undefined;
    }

    if (!parsed.version) {
      console.warn(`[safeCookie]: No version found in cookie [${keyWithVersion.key}], clearing...`);
      removeItem({ keyWithVersion });
      return undefined;
    }

    if (parsed.version === keyWithVersion.version) {
      return parsed.data as T;
    }

    if (migrationConfig?.migrate) {
      console.warn(
        `[safeCookie]: Migrating cookie [${keyWithVersion.key}] from v${parsed.version} to v${keyWithVersion.version}`
      );

      try {
        const migratedData = migrationConfig.migrate(
          parsed.data,
          parsed.version,
          keyWithVersion.version
        );

        setItem({ keyWithVersion, value: migratedData });

        return migratedData;
      } catch (error) {
        console.error(`[safeCookie]: Migration failed for [${keyWithVersion.key}]:`, error);
        removeItem({ keyWithVersion });
        return undefined;
      }
    }

    console.warn(
      `[safeCookie]: Version mismatch in cookie [${keyWithVersion.key}]: expected ${keyWithVersion.version}, got ${parsed.version}. Clearing...`
    );

    removeItem({ keyWithVersion });

    return undefined;
  } catch (error) {
    console.error(`[safeCookie]: Failed to parse cookie [${keyWithVersion.key}]:`, error);
    removeItem({ keyWithVersion });
    return undefined;
  }
};

const removeItem = (args: {
  keyWithVersion: Pick<SafeCookieTypes.KeyWithVersion, 'key'>;
}): void => {
  const { keyWithVersion } = args;
  const cookie = useCookie(keyWithVersion.key);
  cookie.value = null;
};

const hasItem = (args: { keyWithVersion: SafeCookieTypes.KeyWithVersion }): boolean => {
  return getItem(args) !== undefined;
};

export const safeCookie = {
  setItem,
  getItem,
  removeItem,
  hasItem,
} as const;
