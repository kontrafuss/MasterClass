from django.urls import path
from django.views.generic import TemplateView

from . import views
from .views import *

urlpatterns = [
    path('', TemplateView.as_view(template_name = 'resources/index.html'), name='home'),
    path('timetable/', TimetableIndex.as_view(), name='timetable-index'),
    path('timetable/<int:resource>', Timetable.as_view(), name='timetable'),
    path('timetable/role/<int:role>', Timetable.as_view(), name='timetable-all'),
    path('calendar/<int:role>', CalendarView.as_view(), name='calendar'),
    path('conflicts/<int:resource>', ConflictList.as_view()),

    path('resource/<int:pk>', ResourceView.as_view(), name="resource"),
    path('resource/<int:pk>/dependency/<int:dependency>', ResourceDependenciesView.as_view(), name='resource-dependency'),

    path('json/events/', EventsJSON.as_view(), name='events-json'),
    path('json/events/<int:role>', EventsJSON.as_view(), name='events-by-role-json'),
    path('json/resources/<int:role>', ResourcesJSON.as_view(), name='resources-by-role-json'),
    path('json/resources/', ResourcesJSON.as_view(), name='resources-json'),
    path('json/conflicts/', ConflictsJSON.as_view(), name='conflicts-json'),
]
