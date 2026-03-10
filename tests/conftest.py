import pytest
from django.test import override_settings


# 테스트 전체에 Dummy Cache 적용 (Redis 없이 테스트 가능)
@pytest.fixture(autouse=True)
def use_dummy_cache(settings):
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
