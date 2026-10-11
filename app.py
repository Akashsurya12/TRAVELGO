from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from decimal import Decimal
import uuid
import random

# Import local database and SNS fallback layer
from local_storage import LocalDynamoDBResource, LocalSNSClient

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'travelgo_super_secret_session_key_2026')

# AWS Setup / Local Storage Fallback
REGION = os.environ.get('AWS_DEFAULT_REGION', 'ap-south-1')
SNS_TOPIC_ARN = os.environ.get(
    'SNS_TOPIC_ARN',
    'arn:aws:sns:ap-south-1:353250843450:TravelBooking:c491f92a-a668-4b71-aee8-dcfcf990cdef'
)

def init_services():
    """
    Initializes DynamoDB and SNS clients.
    If valid AWS credentials exist and are reachable, uses AWS resources.
    Otherwise, gracefully falls back to local SQLite storage & mock SNS.
    """
    force_local = os.environ.get('FORCE_LOCAL_DB', '0').lower() in ('1', 'true', 'yes')
    if not force_local:
        try:
            boto_session = boto3.Session(region_name=REGION)
            creds = boto_session.get_credentials()
            if creds:
                # Test credentials with a quick STS call
                sts = boto_session.client('sts')
                sts.get_caller_identity()
                dynamodb_res = boto3.resource('dynamodb', region_name=REGION)
                sns_cli = boto3.client('sns', region_name=REGION)
                print("[TravelGo] Connected to AWS DynamoDB & SNS.")
                return dynamodb_res, sns_cli
        except Exception as e:
            print(f"[TravelGo] AWS not available ({e}). Falling back to Local Storage.")

    print("[TravelGo] Using Local SQLite Database & Simulated SNS Notifications.")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'travelgo_data.db')
    return LocalDynamoDBResource(db_path=db_path), LocalSNSClient()

dynamodb, sns_client = init_services()

users_table = dynamodb.Table('travelgo_users')
trains_table = dynamodb.Table('trains')
bookings_table = dynamodb.Table('bookings')

# Function to send SNS notifications
def send_sns_notification(subject, message):
    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except Exception as e:
        print(f"SNS Error: Could not send notification - {e}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not email or not password:
            flash('Email and password are required!', 'error')
            return render_template('register.html')
            
        if confirm_password and password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        existing = users_table.get_item(Key={'email': email})
        if 'Item' in existing:
            flash('Email already exists!', 'error')
            return render_template('register.html')
        
        # Hash password and store user
        hashed_password = generate_password_hash(password)
        users_table.put_item(Item={'email': email, 'name': name, 'password': hashed_password})
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Retrieve user by email (primary key)
        user = users_table.get_item(Key={'email': email})
        
        # Authenticate user
        if 'Item' in user and check_password_hash(user['Item']['password'], password):
            session['email'] = email
            session['name'] = user['Item'].get('name', email.split('@')[0])
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')
            return render_template('login.html', message='Invalid email or password!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('name', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))
    user_email = session['email']
    username = session.get('name', user_email)
    
    # Query bookings for the logged-in user
    response = bookings_table.query(
        KeyConditionExpression=Key('user_email').eq(user_email),
        ScanIndexForward=False # Get most recent bookings first
    )
    bookings = response.get('Items', [])
    
    # Convert Decimal types from DynamoDB to float for display
    for booking in bookings:
        if 'total_price' in booking:
            try:
                booking['total_price'] = float(booking['total_price'])
            except (TypeError, ValueError):
                booking['total_price'] = 0.0
    return render_template('dashboard.html', username=username, bookings=bookings)

@app.route('/train')
def train():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('train.html')

@app.route('/confirm_train_details')
def confirm_train_details():
    if 'email' not in session:
        return redirect(url_for('login'))

    price_str = request.args.get('price', '0')
    persons_str = request.args.get('persons', '1')
    try:
        price_val = Decimal(price_str)
        num_persons = int(persons_str)
    except (ValueError, TypeError):
        price_val = Decimal('0')
        num_persons = 1

    booking_details = {
        'name': request.args.get('name', 'Train'),
        'train_number': request.args.get('trainNumber', ''),
        'source': request.args.get('source', ''),
        'destination': request.args.get('destination', ''),
        'departure_time': request.args.get('departureTime', ''),
        'arrival_time': request.args.get('arrivalTime', ''),
        'price_per_person': price_val,
        'travel_date': request.args.get('date', datetime.now().strftime('%Y-%m-%d')),
        'num_persons': num_persons,
        'item_id': str(request.args.get('trainId', '1')),
        'booking_type': 'train',
        'train_type': request.args.get('train_type', 'Express'),
        'user_email': session['email'],
        'total_price': price_val * num_persons
    }

    response = bookings_table.scan(
        FilterExpression=Attr('item_id').eq(booking_details['item_id']) &
                         Attr('travel_date').eq(booking_details['travel_date']) &
                         Attr('booking_type').eq('train')
    )

    booked_seats = set()
    for b in response.get('Items', []):
        if 'seats_display' in b:
            for s in b['seats_display'].split(','):
                s_clean = s.strip()
                if s_clean:
                    booked_seats.add(s_clean)

    all_seats = [f"S{i}" for i in range(1, 101)] # 100 seats per train
    available_seats = [seat for seat in all_seats if seat not in booked_seats]

    if len(available_seats) < booking_details['num_persons']:
        flash("Not enough seats available. Please try fewer persons or a different train/date.", "error")
        return redirect(url_for("train"))

    seats_for_display = random.sample(available_seats, booking_details['num_persons'])
    booking_details['proposed_seats_display'] = ', '.join(seats_for_display)
    session['pending_booking'] = booking_details
    
    return render_template('confirm_train_details.html', booking=booking_details, available_seats_display=seats_for_display)

@app.route('/final_confirm_train_booking', methods=['POST'])
def final_confirm_train_booking():
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    booking_data = session.pop('pending_booking', None)
    if not booking_data:
        return jsonify({'success': False, 'message': 'No pending booking found or session expired'}), 400
    
    response = bookings_table.scan(
        FilterExpression=Attr('item_id').eq(booking_data['item_id']) &
                         Attr('travel_date').eq(booking_data['travel_date']) &
                         Attr('booking_type').eq('train')
    )

    booked_seats_current = set()
    for b in response.get('Items', []):
        if 'seats_display' in b:
            for s in b['seats_display'].split(','):
                s_clean = s.strip()
                if s_clean:
                    booked_seats_current.add(s_clean)

    all_seats = [f"S{i}" for i in range(1, 101)]
    available_seats_current = [seat for seat in all_seats if seat not in booked_seats_current]

    if len(available_seats_current) < booking_data['num_persons']:
        return jsonify({'success': False, 'message': 'Not enough seats available. Another booking might have taken them.'}), 400

    allocated_seats = random.sample(available_seats_current, booking_data['num_persons'])
    booking_data['seats_display'] = ', '.join(allocated_seats)
    booking_data['booking_id'] = str(uuid.uuid4())
    booking_data['booking_date'] = datetime.now().isoformat()

    try:
        bookings_table.put_item(Item=booking_data)
    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify({'success': False, 'message': f'Failed to confirm booking due to database error: {e}'}), 500

    # Send SNS notification
    send_sns_notification(
        subject="Train Booking Confirmed",
        message=f"Dear {booking_data['user_email']},\nYour train booking for {booking_data['name']} (Train No: {booking_data['train_number']}) from {booking_data['source']} to {booking_data['destination']} on {booking_data['travel_date']} is confirmed.\nYour allocated seats are: {booking_data['seats_display']}\nTotal Price: ₹{booking_data['total_price']}"
    )

    flash('Train booking confirmed successfully!', 'success')
    return jsonify({'success': True, 'message': 'Train booking confirmed successfully!', 'redirect': url_for('dashboard')})

@app.route('/bus')
def bus():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('bus.html')

@app.route('/confirm_bus_details')
def confirm_bus_details():
    if 'email' not in session:
        return redirect(url_for('login'))

    price_str = request.args.get('price', '0')
    persons_str = request.args.get('persons', '1')
    try:
        price_val = Decimal(price_str)
        num_persons = int(persons_str)
    except (ValueError, TypeError):
        price_val = Decimal('0')
        num_persons = 1

    booking_details = {
        'name': request.args.get('name', 'Bus'),
        'source': request.args.get('source', ''),
        'destination': request.args.get('destination', ''),
        'time': request.args.get('time', ''),
        'type': request.args.get('type', 'Standard'),
        'price_per_person': price_val,
        'travel_date': request.args.get('date', datetime.now().strftime('%Y-%m-%d')),
        'num_persons': num_persons,
        'item_id': str(request.args.get('busId', '1')),
        'booking_type': 'bus',
        'user_email': session['email'],
        'total_price': price_val * num_persons
    }
    
    session['pending_booking'] = booking_details
    return redirect(url_for('select_bus_seats',
                            name=booking_details['name'],
                            source=booking_details['source'],
                            destination=booking_details['destination'],
                            time=booking_details['time'],
                            type=booking_details['type'],
                            price=str(booking_details['price_per_person']),
                            date=booking_details['travel_date'],
                            persons=str(booking_details['num_persons']),
                            busId=booking_details['item_id']))

@app.route('/select_bus_seats')
def select_bus_seats():
    if 'email' not in session:
        return redirect(url_for('login'))

    booking = session.get('pending_booking', {})
    if not booking:
        price_str = request.args.get('price', '0')
        persons_str = request.args.get('persons', '1')
        try:
            price_val = Decimal(price_str)
            num_persons = int(persons_str)
        except (ValueError, TypeError):
            price_val = Decimal('0')
            num_persons = 1

        booking = {
            'name': request.args.get('name', 'Bus'),
            'source': request.args.get('source', ''),
            'destination': request.args.get('destination', ''),
            'time': request.args.get('time', ''),
            'type': request.args.get('type', ''),
            'price_per_person': price_val,
            'travel_date': request.args.get('date', datetime.now().strftime('%Y-%m-%d')),
            'num_persons': num_persons,
            'item_id': str(request.args.get('busId', '1')),
            'booking_type': 'bus',
            'user_email': session['email'],
            'total_price': price_val * num_persons
        }
        session['pending_booking'] = booking

    response = bookings_table.scan(
        FilterExpression=Attr('item_id').eq(booking['item_id']) &
                         Attr('travel_date').eq(booking['travel_date']) &
                         Attr('booking_type').eq('bus')
    )

    booked_seats = set()
    for b in response.get('Items', []):
        if 'seats_display' in b:
            for s in b['seats_display'].split(','):
                s_clean = s.strip()
                if s_clean:
                    booked_seats.add(s_clean)

    all_seats = [f"S{i}" for i in range(1, 41)] # 40 seats per bus
    return render_template("select_bus_seats.html", booking=booking, booked_seats=booked_seats, all_seats=all_seats)

@app.route('/final_confirm_bus_booking', methods=['POST'])
def final_confirm_bus_booking():
    if 'email' not in session:
        return redirect(url_for('login'))

    booking = session.pop('pending_booking', None)
    selected_seats_str = request.form.get('selected_seats', '')
    selected_seats = [s.strip() for s in selected_seats_str.split(',') if s.strip()]
    
    if not booking or not selected_seats:
        flash("Booking failed! Missing seat data or session expired.", "error")
        return redirect(url_for("bus"))

    # Re-check seat availability to prevent double booking
    response = bookings_table.scan(
        FilterExpression=Attr('item_id').eq(booking['item_id']) &
                         Attr('travel_date').eq(booking['travel_date']) &
                         Attr('booking_type').eq('bus')
    )
    existing_booked_seats = set()
    for b in response.get('Items', []):
        if 'seats_display' in b:
            for s in b['seats_display'].split(','):
                s_clean = s.strip()
                if s_clean:
                    existing_booked_seats.add(s_clean)

    if any(s in existing_booked_seats for s in selected_seats):
        flash("One or more selected seats are already booked. Please choose other seats.", "error")
        session['pending_booking'] = booking
        return redirect(url_for('select_bus_seats', 
                                name=booking['name'],
                                source=booking['source'],
                                destination=booking['destination'],
                                time=booking['time'],
                                type=booking['type'],
                                price=str(booking['price_per_person']),
                                date=booking['travel_date'],
                                persons=str(booking['num_persons']),
                                busId=booking['item_id']))

    booking['seats_display'] = ', '.join(selected_seats)
    booking['booking_id'] = str(uuid.uuid4())
    booking['booking_date'] = datetime.now().isoformat()

    try:
        bookings_table.put_item(Item=booking)
    except Exception as e:
        print(f"Database Error: {e}")
        flash(f"Failed to confirm bus booking due to database error: {e}", 'error')
        return redirect(url_for("bus"))
    
    send_sns_notification(
        subject="Bus Booking Confirmed",
        message=f"Dear {booking['user_email']},\nYour bus from {booking['source']} to {booking['destination']} on {booking['travel_date']} at {booking['time']} ({booking['type']}) is confirmed.\nYour selected seats are: {booking['seats_display']}\nTotal Price: ₹{booking['total_price']}"
    )

    flash('Bus booking confirmed successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/flight')
def flight():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('flight.html')

@app.route('/confirm_flight_details')
def confirm_flight_details():
    if 'email' not in session:
        return redirect(url_for('login'))
        
    price_str = request.args.get('price', '0')
    pax_str = request.args.get('passengers', '1')
    try:
        price_val = Decimal(price_str)
        pax_val = int(pax_str)
    except (ValueError, TypeError):
        price_val = Decimal('0')
        pax_val = 1

    booking = {
        'flight_id': request.args.get('flight_id', 'FLT001'),
        'airline': request.args.get('airline', 'Airline'),
        'flight_number': request.args.get('flight_number', ''),
        'source': request.args.get('source', ''),
        'destination': request.args.get('destination', ''),
        'departure_time': request.args.get('departure', ''),
        'arrival_time': request.args.get('arrival', ''),
        'travel_date': request.args.get('date', datetime.now().strftime('%Y-%m-%d')),
        'num_persons': pax_val,
        'price_per_person': price_val,
        'total_price': price_val * pax_val
    }
    session['pending_booking'] = booking
    return render_template('confirm_flight_details.html', booking=booking)

@app.route('/confirm_flight_booking', methods=['POST'])
def confirm_flight_booking():
    if 'email' not in session:
        return redirect(url_for('login'))

    booking = session.pop('pending_booking', None)
    if not booking:
        # Fallback to form data
        try:
            price_val = Decimal(request.form.get('price_per_person', '0'))
            pax_val = int(request.form.get('num_persons', '1'))
            booking = {
                'flight_id': request.form.get('flight_id', 'FLT001'),
                'airline': request.form.get('airline', 'Airline'),
                'flight_number': request.form.get('flight_number', ''),
                'source': request.form.get('source', ''),
                'destination': request.form.get('destination', ''),
                'departure_time': request.form.get('departure_time', ''),
                'arrival_time': request.form.get('arrival_time', ''),
                'travel_date': request.form.get('travel_date', datetime.now().strftime('%Y-%m-%d')),
                'num_persons': pax_val,
                'price_per_person': price_val,
                'total_price': price_val * pax_val
            }
        except Exception:
            flash("Flight booking failed! Missing data or session expired.", "error")
            return redirect(url_for('flight'))
        
    booking['user_email'] = session['email']
    booking['booking_date'] = datetime.now().isoformat()
    booking['booking_id'] = str(uuid.uuid4())
    booking['booking_type'] = 'flight'

    try:
        bookings_table.put_item(Item=booking)
    except Exception as e:
        print(f"Database Error: {e}")
        flash(f"Failed to confirm flight booking due to database error: {e}", 'error')
        return redirect(url_for("flight"))

    send_sns_notification(
        subject="Flight Booking Confirmed",
        message=f"Dear {booking['user_email']},\nYour flight booking on {booking['travel_date']} from {booking['source']} to {booking['destination']} with {booking['airline']} (Flight No: {booking['flight_number']}) is confirmed.\nTotal Price: ₹{booking['total_price']}"
    )

    flash('Flight booking confirmed successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/hotel')
def hotel():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('hotel.html')

@app.route('/confirm_hotel_details')
def confirm_hotel_details():
    if 'email' not in session:
        return redirect(url_for('login'))

    price_str = request.args.get('price', '0')
    rooms_str = request.args.get('rooms', '1')
    guests_str = request.args.get('guests', '1')
    rating_str = request.args.get('rating', '3')

    try:
        price_val = Decimal(price_str)
        rooms_val = int(rooms_str)
        guests_val = int(guests_str)
        rating_val = int(rating_str)
    except (ValueError, TypeError):
        price_val = Decimal('0')
        rooms_val = 1
        guests_val = 1
        rating_val = 3

    booking = {
        'name': request.args.get('name', 'Hotel'),
        'location': request.args.get('location', ''),
        'checkin_date': request.args.get('checkin', ''),
        'checkout_date': request.args.get('checkout', ''),
        'num_rooms': rooms_val,
        'num_guests': guests_val,
        'price_per_night': price_val,
        'rating': rating_val
    }

    try:
        ci = datetime.fromisoformat(booking['checkin_date'])
        co = datetime.fromisoformat(booking['checkout_date'])
        nights = (co - ci).days
        if nights <= 0:
            flash("Check-out date must be after check-in date.", "error")
            return redirect(url_for('hotel'))
        booking['nights'] = nights
        booking['total_price'] = booking['price_per_night'] * booking['num_rooms'] * nights
    except (ValueError, TypeError):
        flash("Invalid dates provided.", "error")
        return redirect(url_for('hotel'))

    session['pending_booking'] = booking
    return render_template('confirm_hotel_details.html', booking=booking)

@app.route('/confirm_hotel_booking', methods=['POST'])
def confirm_hotel_booking():
    if 'email' not in session:
        return redirect(url_for('login'))

    booking = session.pop('pending_booking', None)
    if not booking:
        try:
            checkin = request.form.get('checkin', '')
            checkout = request.form.get('checkout', '')
            ci = datetime.fromisoformat(checkin)
            co = datetime.fromisoformat(checkout)
            nights = max(1, (co - ci).days)
            rooms = int(request.form.get('rooms', 1))
            price = Decimal(request.form.get('price', '0'))
            booking = {
                'name': request.form.get('hotel_name', 'Hotel'),
                'location': request.form.get('location', ''),
                'checkin_date': checkin,
                'checkout_date': checkout,
                'num_rooms': rooms,
                'num_guests': int(request.form.get('guests', 1)),
                'price_per_night': price,
                'rating': int(request.form.get('rating', 3)),
                'nights': nights,
                'total_price': price * rooms * nights
            }
        except Exception:
            flash("Hotel booking failed! No pending booking found or session expired.", "error")
            return redirect(url_for('hotel'))

    booking['user_email'] = session['email']
    booking['booking_date'] = datetime.now().isoformat()
    booking['booking_id'] = str(uuid.uuid4())
    booking['booking_type'] = 'hotel'

    try:
        bookings_table.put_item(Item=booking)
    except Exception as e:
        print(f"Database Error: {e}")
        flash(f"Failed to confirm hotel booking due to database error: {e}", 'error')
        return redirect(url_for("hotel"))

    send_sns_notification(
        subject="Hotel Booking Confirmed",
        message=f"Dear {booking['user_email']},\nHotel booking at {booking['name']} in {booking['location']} from {booking['checkin_date']} to {booking['checkout_date']} for {booking['num_rooms']} rooms and {booking['num_guests']} guests is confirmed.\nTotal Price: ₹{booking['total_price']}"
    )

    flash('Hotel booking confirmed successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    if 'email' not in session:
        return redirect(url_for('login'))

    booking_id = request.form.get('booking_id')
    user_email = session['email']
    booking_date = request.form.get('booking_date')

    if not booking_id and not booking_date:
        flash("Error: Booking information is missing for cancellation.", 'error')
        return redirect(url_for('dashboard'))

    try:
        delete_key = {'user_email': user_email}
        if booking_date:
            delete_key['booking_date'] = booking_date
        if booking_id:
            delete_key['booking_id'] = booking_id

        bookings_table.delete_item(Key=delete_key)
        flash("Booking cancelled successfully!", 'success')
    except Exception as e:
        flash(f"Failed to cancel booking: {str(e)}", 'error')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
