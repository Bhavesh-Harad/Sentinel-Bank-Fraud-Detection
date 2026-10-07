/**
 * Simple in-memory cache for API responses.
 * Prevents re-fetching the same data every time you switch modules.
 * Cache expires after 60 seconds.
 */

const CACHE_TTL_MS = 60_000 // 1 minute

interface CacheEntry<T> {
  data: T
  timestamp: number
}

const cache = new Map<string, CacheEntry<unknown>>()

export function getCached<T>(key: string): T | null {
  const entry = cache.get(key) as CacheEntry<T> | undefined
  if (!entry) return null
  if (Date.now() - entry.timestamp > CACHE_TTL_MS) {
    cache.delete(key)
    return null
  }
  return entry.data
}

export function setCached<T>(key: string, data: T): void {
  cache.set(key, { data, timestamp: Date.now() })
}

export function clearCache(key?: string): void {
  if (key) cache.delete(key)
  else cache.clear()
}
