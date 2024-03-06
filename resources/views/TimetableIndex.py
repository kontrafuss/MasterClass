from django.views.generic import ListView

from resources.models import Resource

class TimetableIndex(ListView):
    template_name = 'resources/timetable_index.html'
    model = Resource
    order_by = 'role'
