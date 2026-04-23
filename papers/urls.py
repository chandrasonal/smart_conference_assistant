from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('',                        views.home,             name='index'),
    path('api/search/',             views.search_papers,    name='search_papers'),

    # Auth
    path('login/',                  views.admin_login,      name='admin_login'),
    path('logout/',                 views.admin_logout,     name='admin_logout'),

    # Admin dashboard
    path('dashboard/',              views.admin_dashboard,  name='admin_dashboard'),

    # Admin API endpoints
    path('api/papers/',             views.list_papers,      name='list_papers'),
    path('api/papers/add/',         views.add_paper,        name='add_paper'),
    path('api/papers/<int:paper_id>/delete/', views.delete_paper, name='delete_paper'),
    path('api/papers/upload/',      views.bulk_upload,      name='bulk_upload'),
    path('api/stats/',              views.stats,            name='stats'),
]
