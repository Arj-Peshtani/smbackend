# based on http://anthony-tresontani.github.io/Django/2012/09/20/multilingual-search/
import re
from django.conf import settings
from django.utils import translation
from haystack import connections
from haystack.backends.solr_backend import SolrEngine, SolrSearchBackend, SolrSearchQuery
from haystack.constants import DEFAULT_ALIAS

def get_using(language, alias=DEFAULT_ALIAS):
    new_using = alias + "_" + language
    using = new_using if new_using in settings.HAYSTACK_CONNECTIONS else alias
    return using


class MultilingualSolrSearchBackend(SolrSearchBackend):
    def _multi_backend_run(self, func_name, *args, **kwargs):
        # do not allow calling update on a multilingual backend
        if re.search(r'_[\w]{2}$', self.connection_alias):
            return
        initial_language = translation.get_language()[:2]
        # retrieve unique backend name
        backends = []
        for language, __ in settings.LANGUAGES:
            using = get_using(language, alias=self.connection_alias)
            # Ensure each backend is called only once
            if using in backends:
                continue
            else:
                backends.append(using)
            translation.activate(language)
            backend = connections[using].get_backend()
            print('[%s]' % using)
            func = getattr(super(MultilingualSolrSearchBackend, backend), func_name)
            func(*args, **kwargs)

        translation.activate(initial_language)

    def update(self, index, iterable, commit=True):
        self._multi_backend_run('update', index, iterable, commit=commit)

    def remove(self, obj_or_string, commit=True):
        self._multi_backend_run('remove', obj_or_string, commit=commit)


class MultilingualSolrSearchQuery(SolrSearchQuery):
    def __init__(self, using=DEFAULT_ALIAS):
        language = translation.get_language()[:2]
        using = get_using(language)
        super(MultilingualSolrSearchQuery, self).__init__(using=using)


class MultilingualSolrEngine(SolrEngine):
    backend = MultilingualSolrSearchBackend
    query = MultilingualSolrSearchQuery
