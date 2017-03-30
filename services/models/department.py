from django.db import models

from services.utils import get_translated
from .organization import Organization


class Department(models.Model):
    uuid = models.UUIDField(db_index=True, editable=False)
    business_id = models.CharField(max_length=10)  # take into consideration intl. ids

    # translateable group here
    name = models.CharField(max_length=200, db_index=True)
    abbr = models.CharField(max_length=50, db_index=True, null=True)
    street_address = models.CharField(max_length=100, null=True)
    address_city = models.CharField(max_length=100, null=True)
    address_postal_full = models.CharField(max_length=200, null=True)
    www = models.CharField(max_length=200, null=True)

    phone = models.CharField(max_length=30, null=True)
    address_zip = models.CharField(max_length=10, null=True)
    hierarchy_level = models.SmallIntegerField(null=True)
    object_identifier = models.CharField(max_length=20, null=True)

    organization = models.ForeignKey(Organization, null=True)
    organization_type = models.CharField(max_length=50, null=True)

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)
