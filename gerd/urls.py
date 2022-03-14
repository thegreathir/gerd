"""gerd URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework.authtoken import views
from rest_framework.documentation import include_docs_urls

from core.views import (RoomDetail, RoomList, correct, get_ticket, join_room,
                        play, rearrange, skip, start_match, test)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/', include_docs_urls(title='Gerd API')),
    path('api-token-auth/', views.obtain_auth_token),
    path('rooms/', RoomList.as_view(), name='rooms'),
    path('rooms/<int:pk>/', RoomDetail.as_view(), name='room-detail'),
    path('rooms/<int:pk>/join', join_room, name='join-room'),
    path('rooms/<int:pk>/start', start_match, name='start-room-match'),
    path('rooms/<int:pk>/play', play, name='play'),
    path('rooms/<int:pk>/correct', correct, name='correct'),
    path('rooms/<int:pk>/skip', skip, name='skip'),
    path('rooms/<int:pk>/rearrange', rearrange, name='rearrange'),
    path('rooms/<int:pk>/ticket', get_ticket, name='get_ticket'),

    path('test/<int:pk>/', test, name='test'),
]
