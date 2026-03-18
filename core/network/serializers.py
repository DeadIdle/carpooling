from rest_framework import serializers
from .models import CarpoolRequest, Node

class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ['id', 'location']

class CarpoolRequestSerializer(serializers.ModelSerializer):
    passenger = serializers.StringRelatedField()
    pickup_node = NodeSerializer()
    dropoff_node = NodeSerializer()

    class Meta:
        model = CarpoolRequest
        fields = ['id', 'passenger', 'pickup_node', 'dropoff_node', 'status', 'created_at']