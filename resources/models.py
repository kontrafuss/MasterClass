from django.db import models


class Role(models.Model):
    label = models.CharField(max_length=64)
    plural_label = models.CharField(max_length=64)
    weight = models.SmallIntegerField(default=0)

    class Meta:
        ordering = ['weight', 'label']

    def __str__(self):
        return self.label

class Resource(models.Model):
    label = models.CharField(max_length=127)
    description = models.TextField(blank=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    dependencies = models.ManyToManyField("self", symmetrical=False, blank=True)

    class Meta:
        ordering = ["role","label"]

    def __str__(self):
        return self.label

    def ancestors(self):
        # TODO return list of objects instead of ids
        return [r.id for r in Resource.objects.raw(
            'WITH RECURSIVE parent(id) AS ( \
                VALUES(%s) UNION \
                SELECT from_resource_id \
                FROM resources_resource_dependencies AS d, parent \
                WHERE d.to_resource_id=parent.id \
            ) \
            SELECT id FROM resources_resource AS res WHERE res.id IN parent;',
            [self.id] )]

    def descendants(self):
        return list(Resource.objects.raw(
            'WITH RECURSIVE child(id) AS ( \
                VALUES(%s) UNION \
                SELECT to_resource_id \
                FROM resources_resource_dependencies AS d, child \
                WHERE d.from_resource_id=child.id \
            ) \
            SELECT id FROM resources_resource AS res WHERE res.id IN child;',
            [self.id] ))


class Event(models.Model):
    FULLDATETIME_FMT = "%d.%m.%Y %H:%M"
    TIME_FMT = "%H:%M"

    label = models.CharField(max_length=64, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    is_global = models.BooleanField(default=False)
    dependencies = models.ManyToManyField(Resource, blank=True)

    class Meta:
        ordering = ['start', 'end']

    def __str__(self):
        if self.is_global:
            res = "*"
        else:
            res = ' - '.join([d.label for d in self.dependencies.order_by('role')])

        if self.label:
            res = "%s %s" % (self.label, res)

        start = self.start.strftime(self.FULLDATETIME_FMT)
        if self.start.date() == self.end.date():
            end = self.end.strftime(self.TIME_FMT)
        else:
            end = self.end.strftime(self.FULLDATETIME_FMT)

        return '%s-%s: %s' % (start, end, res)


    def find_conflicts(self):
        conflicts = set()
        related_self = set()
        for d in self.dependencies.all():
            related_self |= set(d.descendants())

        for other in Event.objects.exclude(id=self.id).filter(end__gt=self.start, start__lt=self.end):
            related_other = set()
            for d in other.dependencies.all():
                related_other |= set(d.descendants())

            conflicts |= (related_self & related_other)

        return conflicts



    # for resource in Resource.objects.all():
    #     related_resources = resource.ancestors()
    #     events = list( Event.objects.filter(dependencies__in=related_resources).order_by('start') )
    #
    #     previous_event = None
    #     for event in events:
    #         if (previous_event):
    #             gap = event.start - previous_event.end
    #
    #             if (gap < timedelta(0)):
    #                 conflicts.append({
    #                     'resource' : resource,
    #                     'first_event' : previous_event,
    #                     'second_event' : event,
    #                 })
    #
    #         previous_event = event
    #
    # return conflicts

