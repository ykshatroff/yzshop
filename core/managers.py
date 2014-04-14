from yz.cache.managers import CachingManager

class StaticBlockManager(CachingManager):
    timeout = 86400
    use_for_related_fields = True
    cache_fields = ['id',]
