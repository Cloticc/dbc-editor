class CacheManager:
    def __init__(self, max_size=5):
        self.cached_data = {}
        self.max_cache_size = max_size

    def get(self, key):
        return self.cached_data.get(key)

    def set(self, key, value):
        if len(self.cached_data) >= self.max_cache_size:
            oldest_key = next(iter(self.cached_data))
            del self.cached_data[oldest_key]
        self.cached_data[key] = value

    def clear(self):
        self.cached_data.clear()
