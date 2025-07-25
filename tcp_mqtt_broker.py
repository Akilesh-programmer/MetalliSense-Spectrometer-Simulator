#!/usr/bin/env python3
"""
TCP-based MQTT Broker for External Client Connections
A simple TCP MQTT broker that can accept connections from Node.js clients.
"""

import socket
import threading
import time
import json
import struct
from typing import Dict, List, Tuple


class SimpleTCPMQTTBroker:
    """
    A simple TCP-based MQTT broker that can accept external connections.
    This is a minimal implementation to support basic MQTT operations.
    """
    
    def __init__(self, host='localhost', port=1883):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.clients: Dict[socket.socket, Dict] = {}
        self.subscriptions: Dict[str, List[socket.socket]] = {}
        self.retained_messages: Dict[str, bytes] = {}
        self.server_thread = None
        
    def start(self):
        """Start the TCP MQTT broker"""
        if self.running:
            return True
            
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            
            self.running = True
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            print(f"✅ TCP MQTT Broker started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start TCP MQTT broker: {e}")
            return False
            
    def stop(self):
        """Stop the TCP MQTT broker"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.server_thread:
            self.server_thread.join(timeout=2)
            
    def _run_server(self):
        """Main server loop"""
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                print(f"📡 New client connected from {address}")
                
                # Initialize client data
                self.clients[client_socket] = {
                    'address': address,
                    'client_id': f'client_{len(self.clients)}',
                    'connected': True
                }
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket,), 
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"❌ Error accepting connection: {e}")
                    
    def _handle_client(self, client_socket):
        """Handle individual client connection"""
        try:
            while self.running and client_socket in self.clients:
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                self._process_mqtt_packet(client_socket, data)
                
        except Exception as e:
            print(f"❌ Error handling client: {e}")
        finally:
            self._disconnect_client(client_socket)
            
    def _process_mqtt_packet(self, client_socket, data):
        """Process MQTT packet (simplified)"""
        if len(data) == 0:
            return
            
        # Very basic MQTT packet processing
        packet_type = (data[0] >> 4) & 0x0F
        
        if packet_type == 1:  # CONNECT
            self._handle_connect(client_socket, data)
        elif packet_type == 3:  # PUBLISH
            self._handle_publish(client_socket, data)
        elif packet_type == 8:  # SUBSCRIBE
            self._handle_subscribe(client_socket, data)
        elif packet_type == 12:  # PINGREQ
            self._handle_pingreq(client_socket)
        elif packet_type == 14:  # DISCONNECT
            self._disconnect_client(client_socket)
            
    def _handle_connect(self, client_socket, data):
        """Handle MQTT CONNECT packet"""
        # Send CONNACK (simplified)
        connack = bytes([0x20, 0x02, 0x00, 0x00])
        client_socket.send(connack)
        print(f"✅ Client {self.clients[client_socket]['address']} connected")
        
    def _handle_publish(self, client_socket, data):
        """Handle MQTT PUBLISH packet (simplified)"""
        try:
            # Simple topic/payload extraction (this is very basic)
            # In a real implementation, you'd properly parse the MQTT protocol
            if len(data) > 4:
                topic_length = struct.unpack('>H', data[2:4])[0]
                if len(data) > 4 + topic_length:
                    topic = data[4:4+topic_length].decode('utf-8')
                    payload = data[4+topic_length:].decode('utf-8')
                    
                    print(f"📨 Published to {topic}: {payload[:50]}...")
                    
                    # Store retained messages
                    self.retained_messages[topic] = data[4+topic_length:]
                    
                    # Forward to subscribers
                    if topic in self.subscriptions:
                        for subscriber in self.subscriptions[topic]:
                            if subscriber != client_socket and subscriber in self.clients:
                                try:
                                    # Send PUBLISH to subscriber (simplified)
                                    subscriber.send(data)
                                except:
                                    pass
                                    
        except Exception as e:
            print(f"❌ Error processing publish: {e}")
            
    def _handle_subscribe(self, client_socket, data):
        """Handle MQTT SUBSCRIBE packet (simplified)"""
        try:
            # Simple subscription handling
            # Extract topic (this is very simplified)
            if len(data) > 6:
                topic_length = struct.unpack('>H', data[4:6])[0]
                if len(data) > 6 + topic_length:
                    topic = data[6:6+topic_length].decode('utf-8')
                    
                    if topic not in self.subscriptions:
                        self.subscriptions[topic] = []
                    
                    if client_socket not in self.subscriptions[topic]:
                        self.subscriptions[topic].append(client_socket)
                        
                    print(f"📡 Client subscribed to: {topic}")
                    
                    # Send SUBACK
                    packet_id = struct.unpack('>H', data[2:4])[0]
                    suback = struct.pack('>BBHB', 0x90, 0x03, packet_id, 0x00)
                    client_socket.send(suback)
                    
                    # Send retained message if available
                    if topic in self.retained_messages:
                        # Create and send PUBLISH for retained message
                        retained_payload = self.retained_messages[topic]
                        topic_bytes = topic.encode('utf-8')
                        publish_packet = struct.pack('>BBH', 0x30, 2 + len(topic_bytes) + len(retained_payload), len(topic_bytes))
                        publish_packet += topic_bytes + retained_payload
                        client_socket.send(publish_packet)
                        
        except Exception as e:
            print(f"❌ Error processing subscribe: {e}")
            
    def _handle_pingreq(self, client_socket):
        """Handle MQTT PINGREQ"""
        # Send PINGRESP
        pingresp = bytes([0xD0, 0x00])
        client_socket.send(pingresp)
        
    def _disconnect_client(self, client_socket):
        """Disconnect a client"""
        if client_socket in self.clients:
            address = self.clients[client_socket]['address']
            del self.clients[client_socket]
            print(f"❌ Client {address} disconnected")
            
            # Remove from subscriptions
            for topic in self.subscriptions:
                if client_socket in self.subscriptions[topic]:
                    self.subscriptions[topic].remove(client_socket)
                    
        try:
            client_socket.close()
        except:
            pass
            
    def publish(self, topic: str, payload: str):
        """Publish a message from server side"""
        try:
            if topic in self.subscriptions:
                topic_bytes = topic.encode('utf-8')
                payload_bytes = payload.encode('utf-8')
                
                # Create PUBLISH packet
                publish_packet = struct.pack('>BBH', 0x30, 2 + len(topic_bytes) + len(payload_bytes), len(topic_bytes))
                publish_packet += topic_bytes + payload_bytes
                
                # Store as retained
                self.retained_messages[topic] = payload_bytes
                
                # Send to all subscribers
                for subscriber in self.subscriptions[topic]:
                    if subscriber in self.clients:
                        try:
                            subscriber.send(publish_packet)
                        except:
                            pass
                            
                print(f"📤 Server published to {topic}: {payload[:50]}...")
                return True
        except Exception as e:
            print(f"❌ Error publishing: {e}")
        return False


# Global broker instance
_broker_instance = None

def start_tcp_mqtt_broker():
    """Start the TCP MQTT broker"""
    global _broker_instance
    if _broker_instance is None:
        _broker_instance = SimpleTCPMQTTBroker()
        return _broker_instance.start()
    return True

def stop_tcp_mqtt_broker():
    """Stop the TCP MQTT broker"""
    global _broker_instance  
    if _broker_instance:
        _broker_instance.stop()
        _broker_instance = None

def get_tcp_mqtt_broker():
    """Get the broker instance"""
    return _broker_instance


if __name__ == "__main__":
    # Test the TCP broker
    broker = SimpleTCPMQTTBroker()
    
    try:
        broker.start()
        print("🚀 TCP MQTT Broker is running...")
        print("Press Ctrl+C to stop")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping TCP MQTT broker...")
        broker.stop()
        print("✅ TCP MQTT broker stopped")
