from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),

    path('join', views.join, name='join'),
    path('create', views.create, name='create'),

    path('host', views.host, name='host'),
    path('room', views.room, name='room'),

    # path('about', views.about, name='about'),

    path('login', views.login, name='login')
]
