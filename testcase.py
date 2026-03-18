from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utiils import get_nodes_within_distance
from .models import Trip, CarpoolRequest
class CRAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request, trip_id):
        trip = Trip.objects.get(id = trip_id)
        remianing_nodes = trip.get_remaining
        possible_nodes = set()
        roadmap = get_roadmap()
        for node in remianing_nodes:
            possible_nodes |= get_nodes_within_distance(roadmap, node_id, 2)
        req = CarpoolRequest.objects.filter(status = 'PENDING')
        
        

    
        