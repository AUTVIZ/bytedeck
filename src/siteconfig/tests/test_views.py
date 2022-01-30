from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.forms.models import model_to_dict
from django.shortcuts import reverse

from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient

from hackerspace_online.tests.utils import ViewTestUtilsMixin
from siteconfig.models import SiteConfig

User = get_user_model()


class SiteConfigModelTest(ViewTestUtilsMixin, TenantTestCase):
    """Tests for the SiteConfig model
    """

    def setUp(self):
        """TenantTestCase generates a tenant for tests.
        Each tenant should have a single SiteConfig object
        that is created upon first access via the get() method.
        """
        self.config = SiteConfig.get()
        self.client = TenantClient(self.tenant)

    def test_SiteConfigUpdateOwn(self):
        """ SiteConfigUpdateOwn is an update view that sets the object to
        this tenants SiteConfig singleton
        """

        # requires staff member
        self.assertRedirectsAdmin('config:site_config_update_own')

        self.client.force_login(User.objects.create_user(username='staff_test', is_staff=True))
        self.assert200('config:site_config_update_own')

    def test_SiteConfigUpdate(self):
        # requires staff member
        self.assertRedirectsAdmin('config:site_config_update', args=[self.config.get().id])

        self.client.force_login(User.objects.create_user(username='staff_test', is_staff=True))
        self.assert200('config:site_config_update', args=[self.config.get().id])

    def testSiteConfigUpdate_uses_newly_saved_cache_data(self):

        self.client.force_login(User.objects.create_user(username='staff_test', is_staff=True))

        old_cache = cache.get(SiteConfig.cache_key())

        data = model_to_dict(old_cache)
        del data['banner_image']
        del data['banner_image_dark']
        del data['site_logo']
        del data['default_icon']
        del data['favicon']

        new_site_name = 'My New Site Name'
        data['site_name'] = new_site_name

        self.client.post(reverse('config:site_config_update_own'), data=data)

        # Cache should be empty at the moment since it was recently deleted via signal
        self.assertIsNone(cache.get(SiteConfig.cache_key()))

        # Call SiteConfig.get() so it sets the cache
        siteconfig = SiteConfig.get()

        # Cache should not be empty
        self.assertIsNotNone(cache.get(SiteConfig.cache_key()))
        # and returns the updated SiteConfig
        self.assertEqual(siteconfig.site_name, new_site_name)

        # After calling SiteConfig.get(), cache should not be equal to the old cache
        # Comparing the `site_name` since Django's Model.__eq__ is comparing `pk`
        self.assertNotEqual(old_cache.site_name, cache.get(SiteConfig.cache_key()).site_name)
