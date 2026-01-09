from django.urls import path
from . import views

urlpatterns = [
    path('prompt-manager/', views.prompt_manager, name='prompt_manager'),
    path('ajax/get-prompt/<int:prompt_id>/', views.get_prompt_ajax, name='get_prompt_ajax'),
    path('ajax/update-prompt/<int:prompt_id>/', views.update_prompt_ajax, name='update_prompt_ajax'),
    path('ajax/test-prompt/', views.test_prompt_ajax, name='test_prompt_ajax'),
]
