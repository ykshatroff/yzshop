from yz.cache.managers import CachingManager

class ServiceManager(CachingManager):

    def active(self):
        """
        The cached list of active services
        """
        return self._cache_result(
                (),
                lambda: self.filter(active=True)
        )
