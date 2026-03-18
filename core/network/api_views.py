from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Trip, CarpoolRequest
from .utils import get_roadmap, get_nodes_within_distance
from .serializers import CarpoolRequestSerializer

class CarpoolRequestListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        try:
            trip = Trip.objects.get(id=trip_id, driver=request.user, status__in=['PLANNED', 'ONGOING'])
        except Trip.DoesNotExist:
            return Response({'error': 'Trip not found'}, status=404)

        remaining_nodes = trip.get_remaining()
        roadmap = get_roadmap()

        possible_nodes = set()
        for node_id in remaining_nodes:
            possible_nodes |= get_nodes_within_distance(roadmap, node_id, 2)

        requests = CarpoolRequest.objects.filter(
            pickup_node_id__in=possible_nodes,
            dropoff_node_id__in=possible_nodes,
            status='PENDING'
        )

        serializer = CarpoolRequestSerializer(requests, many=True)
        return Response(serializer.data)