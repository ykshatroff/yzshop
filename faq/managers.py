from yz.cache.managers import CachingManager, PageCachingManagerMixin

class QuestionManager(PageCachingManagerMixin, CachingManager):

    def active(self):
        """
        Shortcut for returning only 'active' objects
        """
        return self.filter(publish=True)
