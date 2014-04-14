from yz.cache.managers import CachingManager

class NewsManager(CachingManager):

    def get_latest_news(self, limit=5):
        """
        get the latest news to display
        """
        cache_key = self._make_cache_key("latest_news",
                "limit", limit)
        latest_news = self._cache_get(cache_key)
        if latest_news is None:
            latest_news = self.active()[:limit]
            self._cache_set(cache_key, latest_news, mark_used=True)
        return latest_news

    def active(self):
        """
        Shortcut for returning only 'active' objects
        """
        return self.filter(publish=True)


