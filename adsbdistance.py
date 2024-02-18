import requests
from math import radians, sin, cos, sqrt, atan2, degrees

# Function to calculate distance between two GPS points using Haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    # Calculate the change in coordinates
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    # Apply Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Calculate the distance
    distance = R * c
    return distance

# Function to calculate direction (bearing) between two GPS points
def calculate_direction(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    # Calculate the change in coordinates
    dlon = lon2_rad - lon1_rad

    # Calculate direction (bearing) using atan2
    y = sin(dlon) * cos(lat2_rad)
    x = cos(lat1_rad) * sin(lat2_rad) - sin(lat1_rad) * cos(lat2_rad) * cos(dlon)
    direction_rad = atan2(y, x)

    # Convert direction from radians to degrees and normalize to [0, 360)
    direction_deg = (degrees(direction_rad) + 360) % 360
    return direction_deg

# URL of the JSON data
url = "http://192.168.8.132/tar1090/data/aircraft.json"

# GPS location
my_lat = 56.xxxx
my_lon = 10.xxxx

# Send an HTTP GET request to the URL
response = requests.get(url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse JSON response
    aircraft_data = response.json()

    # Iterate through each aircraft
    for aircraft in aircraft_data["aircraft"]:
        # Access aircraft properties
        flight = aircraft.get("flight", "Unknown")
        altitude = aircraft.get("alt_baro", "Unknown")
        latitude = aircraft.get("lat", 0.0)
        longitude = aircraft.get("lon", 0.0)

        # Calculate distance and direction
        distance = calculate_distance(my_lat, my_lon, latitude, longitude)
        direction = calculate_direction(my_lat, my_lon, latitude, longitude)

        print(f"Aircraft {flight}:")
        print(f"  Distance: {distance:.2f} km")
        print(f"  Direction: {direction:.2f} degrees")
else:
    print("Failed to retrieve data:", response.status_code)
