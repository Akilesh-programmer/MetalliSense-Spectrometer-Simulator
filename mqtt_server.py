import paho.mqtt.client as mqtt
import json
import threading
import time
from datetime import datetime
from simulate import simulate_reading

# Fallback options for MQTT broker
try:
    from tcp_mqtt_broker import start_tcp_mqtt_broker, stop_tcp_mqtt_broker, get_tcp_mqtt_broker
    TCP_BROKER_AVAILABLE = True
except ImportError:
    TCP_BROKER_AVAILABLE = False

try:
    from embedded_mqtt import create_embedded_client
    EMBEDDED_AVAILABLE = True
except ImportError:
    EMBEDDED_AVAILABLE = False


class SpectrometerMQTTServer:
    def __init__(self):
        self.client = None
        self.running = False
        self.server_thread = None
        self.use_embedded = False
        
        # Spectrometer configuration
        self.metal_grade = "SG-Iron"
        self.incorrect_elements_count = 2
        self.temperature = 0.0
        self.latest_reading = ""
        
        # MQTT broker settings
        self.broker_host = "localhost"
        self.broker_port = 1883
        self.client_id = "spectrometer_server"
        
        # MQTT topics
        self.topics = {
            'config_metal_grade': 'spectrometer/config/metal_grade',
            'config_incorrect_elements': 'spectrometer/config/incorrect_elements', 
            'data_reading': 'spectrometer/data/reading',
            'data_temperature': 'spectrometer/data/temperature',
            'control_generate_reading': 'spectrometer/control/generate_reading',
            'status': 'spectrometer/status'
        }

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            broker_type = "Embedded MQTT Broker" if self.use_embedded else "External MQTT Broker"
            print(f"✅ MQTT Spectrometer Server connected to {broker_type}")
            print(f"📡 Server running on {self.broker_host}:{self.broker_port}")
            
            # Subscribe to configuration and control topics
            client.subscribe(self.topics['config_metal_grade'])
            client.subscribe(self.topics['config_incorrect_elements'])
            client.subscribe(self.topics['control_generate_reading'])
            
            # Publish initial status
            self.publish_status("ONLINE")
            
            # Print access levels (equivalent to OPC UA access levels)
            print("MetalGrade Access: READ/WRITE")
            print("IncorrectElementsCount Access: READ/WRITE") 
            print("Temperature Access: READ")
            print("LatestReading Access: READ")
            
        else:
            print(f"❌ MQTT connection failed with code {rc}")

    def on_disconnect(self, client, userdata, rc):
        print("🛑 MQTT Spectrometer Server disconnected")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            print(f"[MQTT] Received message on {topic}: {payload}")
            
            if topic == self.topics['config_metal_grade']:
                old_value = self.metal_grade
                self.metal_grade = payload
                print(f"[MQTT] MetalGrade updated from {old_value} to {self.metal_grade}")
                
            elif topic == self.topics['config_incorrect_elements']:
                old_value = self.incorrect_elements_count
                self.incorrect_elements_count = int(payload)
                print(f"[MQTT] IncorrectElementsCount updated from {old_value} to {self.incorrect_elements_count}")
                
            elif topic == self.topics['control_generate_reading']:
                print("[MQTT] Generate reading command received")
                self.generate_reading()
                
        except Exception as e:
            print(f"❌ Error processing MQTT message: {e}")

    def generate_reading(self):
        """Generate a new spectrometer reading and publish to MQTT"""
        try:
            print(f"[DEBUG] generate_reading called with MetalGrade={self.metal_grade}, IncorrectElementsCount={self.incorrect_elements_count}")
            
            # Simulate the reading
            result = simulate_reading(self.metal_grade, self.incorrect_elements_count)
            reading_str = json.dumps(result, indent=2)
            self.latest_reading = reading_str
            self.temperature = result.get("temperature", 0.0)
            
            # Publish the reading data
            self.client.publish(self.topics['data_reading'], reading_str, retain=True)
            self.client.publish(self.topics['data_temperature'], str(self.temperature), retain=True)
            
            print(f"[{datetime.now()}] ✅ Generated Reading for {self.metal_grade}")
            print(f"📊 Reading: {reading_str[:100]}..." if len(reading_str) > 100 else f"📊 Reading: {reading_str}")
            print(f"🌡️ Temperature: {self.temperature}°C")
            
            return result
            
        except Exception as e:
            print(f"❌ Error generating reading: {e}")
            return None

    def publish_status(self, status):
        """Publish server status"""
        if self.client:
            self.client.publish(self.topics['status'], status, retain=True)

    def start(self):
        """Start the MQTT server"""
        if self.running:
            print("⚠️ MQTT Server is already running")
            return True
            
        # Try TCP broker first, then external broker, then embedded
        success = self._try_tcp_broker()
        if not success:
            success = self._try_external_broker()
        if not success and EMBEDDED_AVAILABLE:
            print("🔄 Falling back to embedded MQTT broker...")
            success = self._try_embedded_broker()
            
        if success:
            self.running = True
            # Generate initial reading
            time.sleep(1)  # Wait for connection to stabilize
            self.generate_reading()
            return True
        else:
            print("❌ Failed to start any MQTT broker")
            return False
            
    def _try_tcp_broker(self):
        """Try to start and connect to TCP MQTT broker"""
        if not TCP_BROKER_AVAILABLE:
            return False
            
        try:
            print("🔄 Starting TCP MQTT broker...")
            
            # Start the TCP broker
            if start_tcp_mqtt_broker():
                # Give it time to start
                time.sleep(1)
                
                # Create MQTT client
                self.client = mqtt.Client(self.client_id)
                self.client.on_connect = self.on_connect
                self.client.on_disconnect = self.on_disconnect  
                self.client.on_message = self.on_message
                self.use_embedded = False
                
                # Connect to TCP broker
                self.client.connect(self.broker_host, self.broker_port, 60)
                
                # Start the loop in a separate thread
                self.server_thread = threading.Thread(target=self._run_loop, daemon=True)
                self.server_thread.start()
                
                # Wait for connection
                time.sleep(2)
                
                return self.client.is_connected() if hasattr(self.client, 'is_connected') else True
            else:
                return False
                
        except Exception as e:
            print(f"⚠️ TCP broker connection failed: {e}")
            return False
            
    def _try_external_broker(self):
        """Try to connect to external MQTT broker (Mosquitto)"""
        try:
            print(f"🔄 Trying external MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Create MQTT client
            self.client = mqtt.Client(self.client_id)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect  
            self.client.on_message = self.on_message
            self.use_embedded = False
            
            # Connect to broker with timeout
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # Start the loop in a separate thread
            self.server_thread = threading.Thread(target=self._run_loop, daemon=True)
            self.server_thread.start()
            
            # Wait for connection
            time.sleep(2)
            
            return self.client.is_connected() if hasattr(self.client, 'is_connected') else True
            
        except Exception as e:
            print(f"⚠️ External broker connection failed: {e}")
            return False
            
    def _try_embedded_broker(self):
        """Try to use embedded MQTT broker"""
        try:
            print("🔄 Starting embedded MQTT broker...")
            
            # Create embedded client
            self.client = create_embedded_client(self.client_id)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect  
            self.client.on_message = self.on_message
            self.use_embedded = True
            
            # Connect to embedded broker
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            return True
            
        except Exception as e:
            print(f"❌ Embedded broker failed: {e}")
            return False

    def _run_loop(self):
        """Run the MQTT loop"""
        if not self.use_embedded:
            self.client.loop_forever()
        # Embedded client doesn't need explicit loop

    def stop(self):
        """Stop the MQTT server"""
        if not self.running:
            print("⚠️ MQTT Server is not running")
            return
            
        try:
            self.running = False
            
            # Publish offline status
            self.publish_status("OFFLINE")
            
            # Disconnect client
            if self.client:
                self.client.disconnect()
                self.client = None
                
            # Stop TCP broker if we were using it
            if TCP_BROKER_AVAILABLE:
                try:
                    stop_tcp_mqtt_broker()
                except:
                    pass
                
            print("🛑 MQTT Spectrometer Server stopped")
            
        except Exception as e:
            print(f"❌ Error stopping MQTT server: {e}")

    def is_running(self):
        """Check if server is running"""
        return self.running and self.client and self.client.is_connected()

    def get_current_config(self):
        """Get current configuration"""
        return {
            'metal_grade': self.metal_grade,
            'incorrect_elements_count': self.incorrect_elements_count,
            'temperature': self.temperature,
            'latest_reading': self.latest_reading
        }


# For standalone testing
if __name__ == "__main__":
    server = SpectrometerMQTTServer()
    
    try:
        print("🚀 Starting MQTT Spectrometer Server...")
        if server.start():
            print("✅ Server started successfully")
            print("Press Ctrl+C to stop...")
            
            # Keep running
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server.stop()
        print("👋 Server stopped")
