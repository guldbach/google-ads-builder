from django.urls import path
from . import views

app_name = 'usps'

urlpatterns = [
    # USP Manager onepager
    path('manager/', views.usp_manager, name='usp_manager'),
    
    # AJAX endpoints
    path('ajax/create-category/', views.create_category_ajax, name='create_category_ajax'),
    path('ajax/create-usp/', views.create_usp_ajax, name='create_usp_ajax'),
    path('ajax/duplicate-usp/<int:usp_id>/', views.duplicate_usp_ajax, name='duplicate_usp_ajax'),
    path('ajax/edit-category/<int:category_id>/', views.edit_category_ajax, name='edit_category_ajax'),
    path('ajax/edit-usp/<int:usp_id>/', views.edit_usp_ajax, name='edit_usp_ajax'),
    path('ajax/get-usp/<int:usp_id>/', views.get_usp_ajax, name='get_usp_ajax'),
    path('ajax/get-category/<int:category_id>/', views.get_category_ajax, name='get_category_ajax'),
    path('ajax/delete-usp/<int:usp_id>/', views.delete_usp_ajax, name='delete_usp_ajax'),
]