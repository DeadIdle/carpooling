from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Node(models.Model):
    location = models.CharField(max_length=200)
    def __str__(self):
        return f'{self.location}'
    
class User(AbstractUser):
    options = [
        ('DR','Driver'),
        ('PS', 'Passenger'),
        ('AD','Admin')
    ]
    role = models.CharField(max_length=2,choices = options, default='PS')
    mobile_no = models.BigIntegerField(blank=True,null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    #is available to indicated whether the driver is currently available to take the task or not.
    def __str__(self):
        return f'Username - {self.username}'
    
class Trip(models.Model):
    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    start_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='trips_starting')
    end_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='trips_ending')
    current_node = models.ForeignKey(Node, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_trips')
    max_passengers = models.PositiveIntegerField(default=3)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PLANNED')
    created_at = models.DateTimeField(auto_now_add=True)
    route_nodes = models.TextField(default="")
    passed_nodes = models.TextField(default="")

    def get_route(self):
        x = self.route_nodes.split(',')
        final = [int(i) for i in x if i]
        return final
    def get_passed(self):
        return [int(i) for i in self.passed_nodes.split(',') if i]
    def get_remaining(self):
        x= self.get_route()
        y = self.get_passed()
        remaining_nodes = []

        for i in x:
            if i not in y:
                remaining_nodes.append(i)
        return remaining_nodes
    def __str__(self):
        return f'Trip by {self.driver.username}: {self.start_node} → {self.end_node}'

class CarpoolRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), #pending means no driver has offered a ride

        ('OFFERED', 'Offered'), #offered means atleast 1 driver has offered a ride.
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carpool_requests')
    pickup_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='pickups')
    dropoff_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='dropoffs')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Request by {self.passenger.username}: {self.pickup_node} → {self.dropoff_node}'

class Edge(models.Model):
    source = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='to_Go')
    destination = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='to_Reach')
    
    def __str__(self):
        return f'{self.source.location} - {self.destination.location}'
    
class CarpoolOffer(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='offers')
    carpool_request = models.ForeignKey(CarpoolRequest, on_delete=models.CASCADE, related_name='offers')
    detour_nodes = models.IntegerField(default=0)
    fare = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f'Offer from {self.trip.driver.username} for {self.carpool_request}'


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('TOPUP', 'Top Up'),
        ('FARE_DEDUCTION', 'Fare Deduction'),
        ('DRIVER_EARNING', 'Driver Earning'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.transaction_type} of {self.amount} for {self.user.username}'


class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    reviewee = models.ForeignKey(User, on_delete = models.CASCADE, related_name='reviews_recieved')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    comment = models.TextField(max_length=255, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('reviewer', 'trip')
