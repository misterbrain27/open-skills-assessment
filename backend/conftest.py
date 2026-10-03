import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    # Le compteur du throttle vit dans le cache, qui survit d'un test à l'autre : sans ce
    # nettoyage, un test de login pourrait recevoir 429 à cause des tests précédents.
    cache.clear()
