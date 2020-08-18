from django.db import models
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey

from services.utils import get_translated

from .hierarchy import CustomTreeManager
from .keyword import Keyword
from .service import Service
from .unit import Unit


class ServiceNode(MPTTModel):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    parent = TreeForeignKey(
        "self", null=True, related_name="children", on_delete=models.CASCADE
    )
    keywords = models.ManyToManyField(Keyword)

    service_reference = models.TextField(null=True)
    related_services = models.ManyToManyField(Service)

    last_modified_time = models.DateTimeField(
        db_index=True, help_text="Time of last modification"
    )

    objects = CustomTreeManager()
    tree_objects = TreeManager()

    def __str__(self):
        return "%s (%s)" % (get_translated(self, "name"), self.id)

    def get_unit_count(self):
        srv_list = set(
            ServiceNode.objects.all().by_ancestor(self).values_list("id", flat=True)
        )
        srv_list.add(self.id)
        count = (
            Unit.objects.filter(
                public=True, is_active=True, service_nodes__in=list(srv_list)
            )
            .distinct()
            .count()
        )
        return count

    def period_enabled(self):
        """Iterates through related services to find out
        if the tree node has periods enabled via services"""
        return next(
            (o.period_enabled for o in self.related_services.all() if o.period_enabled),
            False,
        )

    class Meta:
        ordering = ["-pk"]
