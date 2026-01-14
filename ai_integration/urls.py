from django.urls import path
from . import views

urlpatterns = [
    # Prompt Manager
    path('prompt-manager/', views.prompt_manager, name='prompt_manager'),
    path('ajax/get-prompt/<int:prompt_id>/', views.get_prompt_ajax, name='get_prompt_ajax'),
    path('ajax/update-prompt/<int:prompt_id>/', views.update_prompt_ajax, name='update_prompt_ajax'),
    path('ajax/test-prompt/', views.test_prompt_ajax, name='test_prompt_ajax'),

    # Loading Widget Manager
    path('loading-widgets/', views.loading_widget_manager, name='loading_widget_manager'),
    path('ajax/get-widget/<int:widget_id>/', views.get_widget_ajax, name='get_widget_ajax'),
    path('ajax/create-widget/', views.create_widget_ajax, name='create_widget_ajax'),
    path('ajax/update-widget/<int:widget_id>/', views.update_widget_ajax, name='update_widget_ajax'),
    path('ajax/delete-widget/<int:widget_id>/', views.delete_widget_ajax, name='delete_widget_ajax'),
    path('ajax/widgets-for-operation/', views.get_widgets_for_operation, name='get_widgets_for_operation'),
]
