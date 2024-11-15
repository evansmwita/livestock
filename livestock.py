import paho.mqtt.client as mqtt
import pandas as pd
import pickle
import random
from twilio.rest import Client
import time

# Load the trained model
model_path = "livestock_health_model.pkl"
with open(model_path, 'rb') as file:
    model = pickle.load(file)

# Twilio Configuration
account_sid = "your_account_sid"  # Replace with your Twilio Account SID
auth_token = "your_auth_token"  # Replace with your Twilio Auth Token
twilio_client = Client(account_sid, auth_token)
twilio_number = "your_twilio_number"  # Replace with your Twilio number
farmer_phone_number = "farmer_phone_number"  # Replace with the farmer's phone number

# MQTT Configuration
broker = "test.mosquitto.org"  # Public broker for testing
port = 1883
topic = "livestock/health_monitor"

# MQTT setup
client = mqtt.Client("LivestockHealthPublisher")
client.connect(broker, port)

# Function to simulate sensor data
def generate_sensor_data():
    temperature = round(random.uniform(98.0, 104.0), 1)
    heart_rate = random.randint(60, 100)
    activity_level = random.choice(["Active", "Inactive"])
    activity_level_encoded = 1 if activity_level == "Active" else 0
    return temperature, heart_rate, activity_level, activity_level_encoded

# Function to simulate GPS coordinates
def get_gps_location():
    latitude = round(random.uniform(-90.0, 90.0), 5)   # Simulate latitude
    longitude = round(random.uniform(-180.0, 180.0), 5)  # Simulate longitude
    return latitude, longitude

# Function to predict health status
def predict_health_status(temperature, heart_rate, activity_level_encoded):
    prediction = model.predict([[temperature, heart_rate, activity_level_encoded]])
    health_status = "Healthy" if prediction[0] == 1 else "Sick"
    return health_status

# Function to send SMS alert to farmer
def send_sms_alert(health_status, latitude, longitude):
    message = f"Alert: Livestock is {health_status}. Location: Lat {latitude}, Long {longitude}."
    sms = twilio_client.messages.create(
        body=message,
        from_=twilio_number,
        to=farmer_phone_number
    )
    print("SMS sent:", sms.sid)

# Publish health data to MQTT broker and send SMS if health status is "Sick"
def publish_health_data():
    temperature, heart_rate, activity_level, activity_level_encoded = generate_sensor_data()
    health_status = predict_health_status(temperature, heart_rate, activity_level_encoded)
    latitude, longitude = get_gps_location()

    # Create message payload
    message = {
        "temperature": temperature,
        "heart_rate": heart_rate,
        "activity_level": activity_level,
        "health_status": health_status,
        "latitude": latitude,
        "longitude": longitude
    }

    # Publish message to the MQTT topic
    client.publish(topic, str(message))
    print("Published:", message)

    # Send SMS alert if livestock is "Sick"
    if health_status == "Sick":
        send_sms_alert(health_status, latitude, longitude)

# Run periodically to simulate data sending
if __name__ == "__main__":
    client.loop_start()
    try:
        while True:
            publish_health_data()
            time.sleep(5)  # Send data every 5 seconds
    except KeyboardInterrupt:
        print("Stopped publishing.")
        client.loop_stop()
        client.disconnect()
