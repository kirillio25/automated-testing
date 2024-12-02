from myapp import views
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('generate-test/', views.generate_test, name='generate_test'),
    path('check-answers/', views.check_answers, name='check_answers'),
    path('download-test-excel/', views.download_test_as_excel, name='download_test_as_excel'),
    path('', lambda request: redirect('generate_test')),  # перенаправление
]