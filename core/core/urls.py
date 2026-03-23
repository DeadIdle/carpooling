from django.contrib import admin
from django.urls import path, include
from network import views
from network import api_views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('accounts/', include('allauth.urls')),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('driver/', views.driver_dashboard, name='driver_dashboard'),
    path('driver/trip/create/', views.create_trip, name='create_trip'),
    path('driver/trip/<int:trip_id>/cancel/', views.cancel_trip, name='cancel_trip'),
    path('passenger/', views.passenger_dashboard, name='passenger_dashboard'),
    path('passenger/request/create/', views.create_request, name='create_request'),
    path('passenger/request/<int:request_id>/offers/', views.view_offers, name='view_offers'),
    path('passenger/request/<int:request_id>/confirm/<int:offer_id>/', views.confirm_offer, name='confirm_offer'),
    path('passenger/request/<int:request_id>/cancel/', views.cancel_request, name='cancel_request'),
    path('driver/trip/<int:trip_id>/requests/', views.view_requests, name='view_requests'),
    path('driver/trip/<int:trip_id>/offer/<int:request_id>/', views.make_offer, name='make_offer'),
    path('api/trips/<int:trip_id>/requests/', api_views.CarpoolRequestListAPI.as_view(), name='api_carpool_requests'),
    path('passenger/wallet/topup/', views.topup_wallet, name='topup_wallet'),
    path('wallet/transactions/', views.transaction_history, name='transaction_history'),
    path('driver/trip/<int:trip_id>/update_node/<int:node_id>/', views.update_current_node, name='update_current_node'),
    path('trip/<int:trip_id>/review/', views.submit_review, name='submit_review'),
    path('trip/<int:trip_id>/review/', views.submit_review, name='submit_review'),
    path('driver/<int:user_id>/profile/', views.driver_profile, name='driver_profile'),
    path('offer/<int:offer_id>/passenger-boarding/', views.passenger_confirms_boarding, name='passenger_confirm_boarding'),
    path('offer/<int:offer_id>/driver-boarding/', views.driver_confirm_boarding, name='driver_confirm_boarding'),
    path('offer/<int:offer_id>/driver-dropoff/', views.driver_confirm_dropoff, name='driver_confirm_dropoff'),
    path('offer/<int:offer_id>/passenger-dropoff/', views.passenger_confirm_dropoff, name='passenger_confirm_dropoff'),
    
]