import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useUiStore } from '../app/shared/model/ui-store';

describe('useUiStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('initializes with isLoading false', () => {
    const store = useUiStore();
    expect(store.isLoading).toBe(false);
  });

  it('setLoading sets isLoading to true', () => {
    const store = useUiStore();
    store.setLoading(true);
    expect(store.isLoading).toBe(true);
  });

  it('setLoading sets isLoading back to false', () => {
    const store = useUiStore();
    store.setLoading(true);
    store.setLoading(false);
    expect(store.isLoading).toBe(false);
  });
});
