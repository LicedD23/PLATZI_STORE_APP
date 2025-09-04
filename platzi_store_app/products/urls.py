from django.urls import path 
from . import views

app_name='products'

urlpatterns=[
    path('',views.products_menu_views,name='products_menu_views'),
    path('add/',views.add_product,name='add_product'),
    path('<int:product_id>/',views.get_product_detail,name='get_product_detail'),
    path('update/<int:product_id>/',views.update_product,name='update_product'),
    path('delete/<int:product_id>/',views.delete_product,name='delete_product'),
    ]