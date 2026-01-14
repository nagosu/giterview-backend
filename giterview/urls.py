"""
URL configuration for giterview project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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

from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from interviews.views import InterviewView
from resumes.views import ResumeView
from users.views import UserView

schema_view = get_schema_view(
    openapi.Info(
        title="TeamA API",
        default_version="v1",
        description="API documentation for Your Project",
        terms_of_service="https://www.yourproject.com/policies/terms/",
        contact=openapi.Contact(email="contact@yourproject.local"),
        license=openapi.License(name="Your Project License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/interviews", InterviewView.as_view(), name="interview-view"),
    path("api/interviews/", include("interviews.urls")),
    path("api/resumes", ResumeView.as_view(), name="resume-view"),
    path("api/resumes/", include("resumes.urls")),
    path("api/users", UserView.as_view(), name="user-view"),
    path("api/users/", include("users.urls")),
    path("", include("django_prometheus.urls")),
]

urlpatterns += [
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
