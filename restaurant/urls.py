from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('chat/send/', views.chat_send, name='chat_send'),
    path('chat/save-response/', views.chat_save_response, name='chat_save_response'),
    path('menu/', views.menu_view, name='menu'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/place/', views.cart_place_order, name='cart_place'),
    path('analytics/', views.analytics_view, name='analytics'),
]
