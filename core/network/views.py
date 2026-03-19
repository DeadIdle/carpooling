from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Node, User, Trip, CarpoolRequest, CarpoolOffer, Transaction, Review
from .utils import get_roadmap, calculate_detour, calculate_fare, get_nodes_within_distance
from .bfs import find_shortest_path
import requests as http_requests
from decimal import Decimal
from django.db.models import Avg
def home(request):
    if request.user.is_authenticated:
        if request.user.role == 'DR':
            return redirect('driver_dashboard')
        elif request.user.role == 'PS':
            return redirect('passenger_dashboard')
    return render(request, 'network/home.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        mobile = request.POST.get('mobile_no') or None

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'network/register.html')

        user = User.objects.create_user(username=username, password=password, role=role, mobile_no=mobile)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        if role == 'DR':
            return redirect('driver_dashboard')
        return redirect('passenger_dashboard')

    return render(request, 'network/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if user.role == 'DR':
                return redirect('driver_dashboard')
            return redirect('passenger_dashboard')
        messages.error(request, 'Invalid credentials.')
    return render(request, 'network/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def driver_dashboard(request):
    if request.user.role != 'DR':
        return redirect('passenger_dashboard')
    active_trips = Trip.objects.filter(driver=request.user, status__in=['PLANNED', 'ONGOING'])
    past_trips = Trip.objects.filter(driver=request.user, status__in=['COMPLETED', 'CANCELLED'])
    
    for trip in active_trips:
        remaining = trip.get_remaining()
        trip.next_node = remaining[1] if len(remaining) > 1 else None

    return render(request, 'network/driver_dashboard.html', {
        'active_trips': active_trips,
        'past_trips': past_trips,
    })
@login_required
def create_trip(request):
    if request.user.role != 'DR':
        return redirect('passenger_dashboard')
    nodes = Node.objects.all()
    if request.method == 'POST':
        start_id = int(request.POST.get('start_node'))
        end_id = int(request.POST.get('end_node'))
        max_passengers = int(request.POST.get('max_passengers', 3))

        road_map = get_roadmap()
        path, _ = find_shortest_path(road_map, start_id, end_id)

        if not path:
            messages.error(request, 'No route found between selected nodes.')
            return render(request, 'network/create_trip.html', {'nodes': nodes})

        trip = Trip.objects.create(
            driver=request.user,
            start_node_id=start_id,
            end_node_id=end_id,
            current_node_id=start_id,
            max_passengers=max_passengers,
            route_nodes=','.join(str(n) for n in path),
            status='PLANNED'
        )
        messages.success(request, 'Trip created successfully!')
        return redirect('driver_dashboard')

    return render(request, 'network/create_trip.html', {'nodes': nodes})

@login_required
def cancel_trip(request, trip_id):
    if request.user.role != 'DR':
        return redirect('passenger_dashboard')
    trip = Trip.objects.get(id=trip_id, driver=request.user)
    if trip.status == 'PLANNED':
        trip.status = 'CANCELLED'
        trip.save()
        messages.success(request, 'Trip cancelled.')
    else:
        messages.error(request, 'Only planned trips can be cancelled.')
    return redirect('driver_dashboard')

@login_required
def passenger_dashboard(request):
    if request.user.role != 'PS':
        return redirect('driver_dashboard')
    

    ongoing_trips = CarpoolRequest.objects.filter(passenger = request.user, status__in =['PENDING', 'OFFERED'])
    cancelled_trips = CarpoolRequest.objects.filter(passenger = request.user, status__in =['CANCELLED'])
    past_trips = CarpoolRequest.objects.filter(passenger = request.user, status__in =['COMPLETED','CONFIRMED'])

    
    return render(request, 'network/passenger_dashboard.html',{'Ongoing_trips' : ongoing_trips,
                                                               
                                                               'Cancelled_trips' : cancelled_trips,
                                                               'Past_trips' : past_trips})

@login_required
def view_offers(request, request_id):
    if request.user.role != 'PS':
        return redirect('driver_dashboard')
    carp_request = CarpoolRequest.objects.get(id = request_id)
    offer = CarpoolOffer.objects.filter(carpool_request = carp_request)
    return render(request, 'network/view_offers.html', {'Offers' : offer,
                                                        'carp_request': carp_request})

@login_required
def confirm_offer(request, request_id, offer_id):
    if request.user.role != 'PS':
        return redirect('driver_dashboard')
    if request.method == 'POST':
        car_request = CarpoolRequest.objects.get(id = request_id, passenger = request.user)
        car_request.status = 'CONFIRMED'
        offer = CarpoolOffer.objects.get(id= offer_id)
        fare = offer.fare
        if fare <= request.user.wallet_balance:
            request.user.wallet_balance -= fare
            offer.trip.driver.wallet_balance += fare
        else :
            messages.error(request, 'Insufficient wallet balance. Please top up.')
            return redirect('view_offers', request_id=request_id)
        Transaction.objects.create(
            user=request.user,
            trip=offer.trip,
            transaction_type='FARE_DEDUCTION',
            amount=fare
        )
        Transaction.objects.create(
            user=offer.trip.driver,
            trip=offer.trip,
            transaction_type='DRIVER_EARNING',
            amount=fare
        )
        offer.status = 'ACCEPTED'
        all_offers = CarpoolOffer.objects.filter(carpool_request = car_request)
        other_offers = all_offers.exclude(id = offer_id)
        other_offers.update(status = 'REJECTED')
        car_request.save()
        request.user.save()
        offer.trip.driver.save()
        offer.save()


    return redirect('passenger_dashboard')
    
@login_required
def cancel_request(request, request_id):
    if request.user.role != 'PS':
        return redirect('driver_dashboard')
    if request.method == 'POST':
        car_request = CarpoolRequest.objects.get(id=request_id, passenger=request.user)
        if car_request.status not in ['CONFIRMED', 'COMPLETED']:
            car_request.status = 'CANCELLED'
            car_request.save()
            CarpoolOffer.objects.filter(carpool_request=car_request).update(status='REJECTED')
    return redirect('passenger_dashboard')

@login_required
def create_request(request):
    if request.user.role != 'PS':
        return redirect('driver_dashboard')
    if request.method == 'POST':
        start_id = request.POST.get('pickup_node')
        end_id = request.POST.get('dropoff_node')
        snode = Node.objects.get(id = start_id)
        enode = Node.objects.get(id = end_id)

        CarpoolRequest.objects.create(
            passenger = request.user,
            pickup_node = snode,
            dropoff_node = enode

        )
        return redirect('passenger_dashboard')
    return render(request, 'network/create_request.html', {'nodes' : Node.objects.all(),
                                       'Passenger' : request.user})
#the dictionary provides the drop down menu.

@login_required
def view_requests(request, trip_id):
    if request.user.role != 'DR':
        return redirect('passenger_dashboard')
    try:
        active_trip = Trip.objects.get(id=trip_id, driver=request.user, status__in=['ONGOING', 'PLANNED'])
        confirmed_passengers = CarpoolOffer.objects.filter(
            trip=active_trip,
            status='ACCEPTED').count()

        if confirmed_passengers >= active_trip.max_passengers:
            return render(request, 'network/view_requests.html', {
                'Requests': [],
                'Active_Trip': active_trip,
                'full': True
            })

        remaining_nodes = active_trip.get_remaining()
        roadmap = get_roadmap()
        possible_nodes = set()
        for node_id in remaining_nodes:
            possible_nodes |= get_nodes_within_distance(roadmap, node_id, 2)

        requests = CarpoolRequest.objects.filter(
            pickup_node_id__in=possible_nodes,
            dropoff_node_id__in=possible_nodes,
            status='PENDING'
        )

        from .serializers import CarpoolRequestSerializer
        serializer = CarpoolRequestSerializer(requests, many=True)

        return render(request, 'network/view_requests.html', {
            'Active_Trip': active_trip,
            'Requests': serializer.data,
        })
    except Trip.DoesNotExist:
        return render(request, 'network/view_requests.html', {'Requests': [], 'Active_Trip': None})
    
@login_required
def make_offer(request,trip_id,request_id):
    if request.user.role != 'DR':
        return redirect('passenger_dashboard')
    if request.method == 'POST':
        activetrip = Trip.objects.get(id=trip_id, driver=request.user, status__in=['ONGOING', 'PLANNED'])
        current_request = CarpoolRequest.objects.get(id = request_id)
        roadmap = get_roadmap()
        remaining_route = activetrip.get_remaining()

        newroute, detourhops = calculate_detour(roadmap, remaining_route, current_request.pickup_node_id, current_request.dropoff_node_id)
        if newroute is None:
            messages.error(request, 'Cannot calculate detour for this request.')
            return redirect('view_requests', trip_id=activetrip.id)
        price = calculate_fare(roadmap,newroute,current_request.pickup_node_id, current_request.dropoff_node_id)
        CarpoolOffer.objects.create(
            trip = activetrip,
            carpool_request = current_request,
            fare = price,
            detour_nodes = detourhops



        )
        current_request.status = 'OFFERED'
        current_request.save()
        return redirect('view_requests',trip_id=activetrip.id)

@login_required
def topup_wallet(request):
    if request.user.role != 'PS':
        return redirect('driver_dashboard')
    if request.method == 'POST':
        amt = Decimal(request.POST.get('amount'))
        request.user.wallet_balance += amt
        Transaction.objects.create(
            user = request.user,
            transaction_type = 'TOPUP',
            amount = amt,


        )
        request.user.save()
        return redirect('passenger_dashboard')
    else :
        return render(request, 'network/topup_wallet.html')

@login_required
def transaction_history(request):
    all_transaction = Transaction.objects.filter(user = request.user)
    return render(request, 'network/transaction_history.html', {'Transactions' : all_transaction})

@login_required
def update_current_node(request, trip_id, node_id):

    if request.user.role != 'DR':
        return redirect('passenger_dashboard')
    if request.method == 'POST':
        trip = Trip.objects.get(driver = request.user,
                                id = trip_id)
        
        trip.current_node = Node.objects.get(id = node_id)
        trip.passed_nodes += f',{node_id}'
        if trip.status == 'PLANNED':
            trip.status = 'ONGOING'
            if trip.current_node == trip.end_node:
                trip.status = 'COMPLETED'
                accepted_requests = CarpoolOffer.objects.filter(trip=trip, status='ACCEPTED').values_list('carpool_request_id', flat=True)
                CarpoolRequest.objects.filter(id__in=accepted_requests).update(status='COMPLETED')
        trip.save()
    return redirect('driver_dashboard')

@login_required
def submit_review(request, trip_id):
    trip = Trip.objects.get(id=trip_id)
    if request.user.role in ['DR', 'PS'] and trip.status == 'COMPLETED':
        if Review.objects.filter(reviewer=request.user, trip=trip).exists():
            messages.error(request, 'You have already reviewed this trip.')
            return redirect('passenger_dashboard')
        else:
            if request.method == 'POST':
                rating = int(request.POST.get('rating'))
                comment = request.POST.get('comment')
                Review.objects.create(
                    reviewer=request.user,
                    reviewee=trip.driver if request.user.role == 'PS' else CarpoolOffer.objects.get(trip=trip, status='ACCEPTED').carpool_request.passenger,
                    rating=rating,
                    comment=comment,
                    trip=trip,
                )
                return redirect('passenger_dashboard' if request.user.role == 'PS' else 'driver_dashboard')
            else:
                return render(request, 'network/submit_review.html', {'trip': trip})
    else:
        messages.error(request, 'You cannot review this trip.')
        return redirect('passenger_dashboard' if request.user.role == 'PS' else 'driver_dashboard')

@login_required
def driver_profile(request,user_id):
        user = User.objects.get(id = user_id)
        reviews = Review.objects.filter(reviewee = user)
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        return render(request, 'network/driver_profile.html', {'Driver' : user,
                                                                 'Reviews' : reviews,
                                                                 'Average_rating' :avg_rating })
