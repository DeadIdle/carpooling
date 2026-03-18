from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Edge, Node, User, Trip, CarpoolRequest, CarpoolOffer, Transaction

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'wallet_balance')
    list_filter = ('role',)

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'location')
    search_fields = ('location',)

@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'source', 'destination')
    list_select_related = ('source', 'destination')
    

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('id', 'driver', 'start_node', 'end_node', 'status')
    list_filter = ('status',)

@admin.register(CarpoolRequest)
class CarpoolRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'passenger', 'pickup_node', 'dropoff_node', 'status')
    list_filter = ('status',)

@admin.register(CarpoolOffer)
class CarpoolOfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'trip', 'carpool_request', 'fare', 'detour_nodes', 'status')
    list_filter = ('status',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'transaction_type', 'amount', 'created_at')
    list_filter = ('transaction_type',)