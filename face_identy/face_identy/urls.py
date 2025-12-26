"""face_identy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.urls import path, re_path
from django.views.static import serve
from django.conf import settings
from controller.FaceController import *
from controller.UserController import *
from controller.DetectionController import *
from controller.AdminController import *

urlpatterns = [
    path('admin/users/', user_getlist),
    path("admin/user_add/",user_add),
    #path("admin/users/<int:currentEditUserId>/",user_update),
    path("admin/users/<int:user_id>/",user_getuser),
    path("admin/users/<int:user_id>/delete/",user_delete),
    path("user/add_face/", add_face),
    path("user/face_collect/", face_collection),
    path("user/face_detect/", face_detection),
    path("user/detection_detect/", predict),
    path("login/",user_login),
    path("user/register/",user_register),
    path("user/update_info/<int:user_id>/", update_user_info),
    path("user/change_password/<int:user_id>/", change_password),
    path('user/save_detection_result/', save_detection_result),
    path('user/record_getlist/',record_getlist),
    path('user/record_clear/',record_clear)
]
