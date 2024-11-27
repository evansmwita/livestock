import streamlit as st
import paho.mqtt.client as mqtt
import pandas as pd
import pickle
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import uuid  # For generating a dynamic client ID

# Load the trained model
@st.cache_resource
def load_model():
    model_path = "model.pkl"
    with open(model_path, 'rb') as file:
        return pickle.load(file)

model = load_model()

# Streamlit UI for configuration
st.title("Livestock Health Monitoring System")

# Email Configuration (Dynamic Input via Streamlit)
st.header("Email Configuration")
smtp_server = st.text_input("SMTP Server", "smtp.gmail.com")
smtp_port = st.number_input("SMTP Port", value=587)
email_user = st.text_input("Your Email Address")
email_password = st.text_input("Your Email Password", type="password")
farmer_email = st.text_input("Farmer's Email Address")

if not all([smtp_server, smtp_port, email_user, email_password, farmer_email]):
    st.warning("Please complete the email configuration.")

# MQTT Configuration
broker = "test.mosquitto.org"  # Public broker for testing
port = 1883
topic = "livestock/health_monitor"

# Generate a unique MQTT client ID dynamically using uuid
client_id = f"LivestockHealthPublisher-{uuid.uuid4().hex[:8]}"

# MQTT setup
client = mqtt.Client(client_id)  # Use the generated unique client ID

# Optional: Define callback functions (you can define more if needed)
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # You can subscribe to a topic here if needed

def on_message(client, userdata, msg):
    print(f"Message received: {msg.payload.decode()}")

# Set the callbacks
client.on_connect = on_connect
client.on_message = on_message

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

# Function to send email alert to farmer
def send_email_alert(health_status, latitude, longitude):
    subject = "Livestock Health Alert"
    body = f"Alert: Livestock is {health_status}. Location: Lat {latitude}, Long {longitude}."
    
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = farmer_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)
        st.success(f"Email sent to: {farmer_email}")
    except Exception as e:
        st.error(f"Failed to send email: {e}")
    finally:
        server.quit()

# Publish health data to MQTT broker and send email if health status is "Sick"
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
    st.write("Published:", message)

    # Send email alert if livestock is "Sick"
    if health_status == "Sick":
        send_email_alert(health_status, latitude, longitude)

# Start Monitoring Button
if st.button("Start Monitoring"):
    client.loop_start()
    try:
        for _ in range(10):  # Simulates 10 cycles
            publish_health_data()
            time.sleep(5)  # Send data every 5 seconds
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        st.write("Stopped publishing.")
