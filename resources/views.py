from django.views.generic import *
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models.functions import Trunc, Lag
from django.db.models import DateTimeField, ExpressionWrapper, fields, Window, F, Q
from .models import *
from datetime import timedelta



DEFAULT_ROLE = 1

def edit_url(id, role):
    if role is None:
        role = DEFAULT_ROLE

    return "%s?source=calendar&role=%s" % (
            reverse('admin:resources_event_change', args=(id,)),
            role )

def delete_url(id):
    return reverse('admin:resources_event_delete', args=(id,))


class CalendarView(ListView):
    template_name = 'resources/calendar.html'
    model = Resource
    context_object_name = 'resources'

    def get_queryset(self):
        primary_role = get_object_or_404(Role, pk=self.kwargs['role'])
        return Resource.objects.order_by('role').exclude(role=primary_role.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['primary_role'] = get_object_or_404(Role, pk=self.kwargs['role'])
        context['roles'] = Role.objects.all()
        context['project'] = Project.objects.get(pk=1)
        return context

    def post(self, request, *args, **kwargs):
        if (('id' in request.POST) and request.POST['id']):
            event = get_object_or_404(Event, pk=request.POST['id'])

            if ('start' in request.POST):
                event.start = request.POST['start']
            if ('end' in request.POST):
                event.end = request.POST['end']
        else:
            event = Event.objects.create(start=request.POST['start'], end=request.POST['end'])

        if ('is_global' in request.POST):
            event.is_global = request.POST['is_global']

        if ('removeResource' in request.POST):
            id = request.POST['removeResource']
            event.dependencies.remove(id)

        if ('resourceIds' in request.POST):
            dependencies = map(int, request.POST['resourceIds'].split(','))
            for id in dependencies: event.dependencies.add(id)

        # TODO allow changing primary resource

        event.save()
        return HttpResponse()


class Timetable(TemplateView):
    template_name = 'resources/timetable.html'

    def view_event(self, event, exclude):
        flatten = lambda l: [item for sublist in l for item in sublist]

        related = flatten([d.descendants() for d in event.dependencies.exclude(id__in=exclude)])
        roles = set(r.role for r in related)

        dependencies = [{
            'role' : role.label,
            'resources' : [r for r in related if r.role.id == role.id],
        } for role in sorted(roles, key=lambda x: x.weight)]

        return {
            'start' : event.start,
            'end' : event.end,
            'label' : event.label,
            'dependencies' : dependencies,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # global flag: whether to display events with is_global==true
        show_globals = bool(int(self.request.GET.get('show_globals', 1)))
        from_date = self.request.GET.get('start', None)
        to_date = self.request.GET.get('end', None)

        # case 1: single resource
        if ('resource' in self.kwargs):
            resources = [ get_object_or_404(Resource, pk=self.kwargs['resource']) ]

        # case 2: all resources for specific role
        elif ('role' in self.kwargs):
            role = get_object_or_404(Role, pk=self.kwargs['role']);
            resources = list( Resource.objects.filter(role=role) )

        else:
            # TODO throw 404
            resources = []


        context['timetables'] = []

        for resource in resources:
            related_resources = resource.ancestors()
            descendants = resource.descendants()

            events = self.get_events(
                related_resources, 
                show_globals=show_globals, 
                from_date=from_date, 
                to_date=to_date)
            dates = set( map( lambda x: x.start.date(), events ))

            events_by_day = []
            for date in sorted(dates):
                events_by_day.append({
                    'date' : date,
                    'events' : [self.view_event(event, exclude=[r.id for r in descendants]) for event in events if event.start.date()==date]
                })

            timetable = {
                'resource' : resource,
                'descendants' : descendants,
                'events_by_day' : events_by_day,
            }

            context['timetables'].append(timetable)

        return context


    def get_events(self, resources, show_globals, from_date, to_date):
        query = Event.objects
        if show_globals:
            query = query.filter(
                Q(is_global=True) | Q(dependencies__in=resources)
            )
        else:
            query = query.filter(dependencies__in=resources)
        if (from_date): query = query.filter(end__gt=from_date)
        if (to_date):   query = query.filter(start__lt=to_date)
        
        return list( query.order_by('start') )



class TimetableIndex(ListView):
    template_name = 'resources/timetable_index.html'
    model = Resource
    order_by = 'role'

from django.db.models import Aggregate, CharField

# class TimetableAll(TemplateView):
#     model = Role


class GroupConcat(Aggregate):
    function = 'GROUP_CONCAT'
    template = '%(function)s(%(distinct)s%(expressions)s%(ordering)s%(separator)s)'

    def __init__(self, expression, distinct=False, ordering=None, separator=',', **extra):
        super(GroupConcat, self).__init__(
            expression,
            distinct='DISTINCT ' if distinct else '',
            ordering=' ORDER BY %s' % ordering if ordering is not None else '',
            separator=',"%s"' % separator,
            output_field=CharField(),
            **extra
        )

"""
List of Events (fullcalendar JSON interface)
"""
class EventsJSON(ListView):
    context_object_name = 'events'

    def get_queryset(self):
        # self.resource = get_object_or_404(Resource, pk=self.kwargs['resource'])
        # related_resources = self.resource.ancestors();
        query = Event.objects

        if ('start' in self.kwargs):
            query = query.filter(end__gt=self.kwargs['start'])

        if ('end' in self.kwargs):
            query = query.filter(start__lt=self.kwargs['end'])

        return query.order_by('start') \
            .annotate(dependencies_ids=GroupConcat('dependencies', separator=','))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # resource = get_object_or_404(Resource, pk=self.kwargs['resource'])
        # context['resource'] = resource
        return context

    def get(self, request, *args, **kwargs):
        if ('role' in kwargs):
            primary_role = get_object_or_404(Role, pk=kwargs['role'])
            primary_resources = [r.id for r in Resource.objects.filter(role=primary_role.id)]
        else:
            primary_role = Role()
            primary_resources = []
        resource_labels = { r.id : r.label for r in Resource.objects.all() }
        label_fn = lambda res : resource_labels[res.id] # TODO fail-safe

        json = []
        for event in self.get_queryset():

            cal_event = {
                'id' : event.id,
                'start' : event.start,
                'end' : event.end,
            }

            dependencies = []
            if event.is_global:
                dependencies = primary_resources
                cal_event['color'] = '#472'
            elif event.dependencies_ids:
                dependencies = list(map(int, str(event.dependencies_ids).split(',')))

            cal_event['resourceIds'] = dependencies

            conflicts = event.find_conflicts()
            if conflicts:
                cal_event['color'] = '#f22'
                cal_event['conflicts'] = '\n'.join(map(label_fn, conflicts))

            if event.label:
                cal_event['title'] = event.label
            else:
                secondary_resources = filter(lambda id: id not in primary_resources, dependencies)
                cal_event['title'] = ', '.join(map(lambda id: resource_labels[id], secondary_resources))

            cal_event['edit_url'] = edit_url(event.id, primary_role.id)
            cal_event['delete_url'] = delete_url(event.id)

            json.append(cal_event)

        return JsonResponse(json, safe=False)

class ResourcesJSON(ListView):
    def get_queryset(self):
        query = Resource.objects
        if ('role' in self.kwargs):
            self.role = get_object_or_404(Role, pk=self.kwargs['role'])
            query = query.filter(role=self.role)
        return query.values('id', title=F('label'))

    def get(self, request, *args, **kwargs):
        data = list(self.get_queryset().values())
        return JsonResponse(data, safe=False)


# RESOURCE_ID EVENT_ID_1 EVENT_ID_2 OVERLAP_START OVERLAP_END

def find_conflicts():
    conflicts = []

    for resource in Resource.objects.all():
        related_resources = resource.ancestors()
        events = list( Event.objects.filter(dependencies__in=related_resources).order_by('start') )

        previous_event = None
        for event in events:
            if (previous_event):
                gap = event.start - previous_event.end
                
                if (gap < timedelta(0)):
                    conflicts.append({
                        'resource' : resource,
                        'first_event' : previous_event,
                        'second_event' : event,
                    })

            previous_event = event

    return conflicts


# TODO unused
class ConflictList(TemplateView):
    template_name = 'resources/conflict_list.html'

    def get_context_data(self, **kwargs):
        # gap = ExpressionWrapper(
        #     F('start') - Window(Lag(F('end'), default='start', order_by='start')), output_field=fields.DurationField() )

        context = super().get_context_data(**kwargs)
        context['conflicts'] = find_conflicts()

        return context

# TODO unused
class ConflictsJSON(View):
    def get(self, request, *args, **kwargs):
        conflicts = map(lambda c: {
            'resource': c['resource'].id,
            'first_event': c['first_event'].id,
            'second_event': c['second_event'].id}, find_conflicts() )
        return JsonResponse(list(conflicts), safe=False)
