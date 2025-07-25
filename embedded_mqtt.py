#!/usr/bin/env python3
"""
Embedded MQTT Broker for Development
A simple MQTT broker that runs embedded with the application for easy development.
"""

import threading
import time
import queue
import json
from typing import Dict, List, Callable
from dataclasses import dataclass


@dataclass
class MQTTMessage:
    topic: str
    payload: str
    retain: bool = False


class EmbeddedMQTTBroker:
    """
    A simple embedded MQTT broker for development purposes.
    This runs in-process and doesn't require external Mosquitto installation.
    """
    
    def __init__(self):
        self.running = False
        self.subscribers: Dict[str, List[Callable]] = {}
        self.retained_messages: Dict[str, str] = {}
        self.message_queue = queue.Queue()
        self.broker_thread = None
        
    def start(self):
        """Start the embedded broker"""
        if self.running:
            return True
            
        self.running = True
        self.broker_thread = threading.Thread(target=self._run_broker, daemon=True)
        self.broker_thread.start()
        print("✅ Embedded MQTT Broker started")
        return True
        
    def stop(self):
        """Stop the embedded broker"""
        self.running = False
        if self.broker_thread:
            self.broker_thread.join(timeout=1)
        print("🛑 Embedded MQTT Broker stopped")
        
    def _run_broker(self):
        """Main broker loop"""
        while self.running:
            try:
                # Process messages from queue
                try:
                    message = self.message_queue.get(timeout=0.1)
                    self._deliver_message(message)
                except queue.Empty:
                    continue
            except Exception as e:
                print(f"❌ Broker error: {e}")
                
    def _deliver_message(self, message: MQTTMessage):
        """Deliver message to subscribers"""
        # Store retained messages
        if message.retain:
            self.retained_messages[message.topic] = message.payload
            
        # Find matching subscribers
        for topic_pattern, callbacks in self.subscribers.items():
            if self._topic_matches(message.topic, topic_pattern):
                for callback in callbacks:
                    try:
                        callback(message.topic, message.payload)
                    except Exception as e:
                        print(f"❌ Subscriber callback error: {e}")
                        
    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """Check if topic matches pattern (supports # and + wildcards)"""
        if pattern == "#":
            return True
        if pattern == topic:
            return True
        if "#" in pattern:
            prefix = pattern.replace("#", "")
            return topic.startswith(prefix)
        return False
        
    def publish(self, topic: str, payload: str, retain: bool = False):
        """Publish a message"""
        message = MQTTMessage(topic, payload, retain)
        self.message_queue.put(message)
        
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
        
        # Deliver retained messages
        for retained_topic, retained_payload in self.retained_messages.items():
            if self._topic_matches(retained_topic, topic):
                callback(retained_topic, retained_payload)
                
    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe from a topic"""
        if topic in self.subscribers:
            try:
                self.subscribers[topic].remove(callback)
                if not self.subscribers[topic]:
                    del self.subscribers[topic]
            except ValueError:
                pass


# Global embedded broker instance
_embedded_broker = None


class EmbeddedMQTTClient:
    """
    MQTT Client that works with the embedded broker
    Compatible with paho-mqtt client interface
    """
    
    def __init__(self, client_id: str = None):
        self.client_id = client_id or f"client_{int(time.time())}"
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        self.connected = False
        self._subscriptions = {}
        
    def connect(self, host: str, port: int = 1883, keepalive: int = 60):
        """Connect to embedded broker"""
        global _embedded_broker
        
        if _embedded_broker is None:
            _embedded_broker = EmbeddedMQTTBroker()
            _embedded_broker.start()
            
        self.connected = True
        if self.on_connect:
            self.on_connect(self, None, None, 0)  # rc=0 means success
            
    def disconnect(self):
        """Disconnect from broker"""
        self.connected = False
        if self.on_disconnect:
            self.on_disconnect(self, None, 0)
            
    def publish(self, topic: str, payload: str, retain: bool = False):
        """Publish message"""
        if not self.connected:
            return
        _embedded_broker.publish(topic, payload, retain)
        
    def subscribe(self, topic: str):
        """Subscribe to topic"""
        if not self.connected:
            return
            
        def message_callback(msg_topic, msg_payload):
            if self.on_message:
                # Create a mock message object
                class MockMessage:
                    def __init__(self, topic, payload):
                        self.topic = topic
                        self.payload = payload.encode('utf-8')
                        
                self.on_message(self, None, MockMessage(msg_topic, msg_payload))
                
        self._subscriptions[topic] = message_callback
        _embedded_broker.subscribe(topic, message_callback)
        
    def unsubscribe(self, topic: str):
        """Unsubscribe from topic"""
        if topic in self._subscriptions:
            _embedded_broker.unsubscribe(topic, self._subscriptions[topic])
            del self._subscriptions[topic]
            
    def loop_forever(self):
        """Keep client running (for compatibility)"""
        while self.connected:
            time.sleep(0.1)
            
    def loop_start(self):
        """Start background loop (for compatibility)"""
        pass
        
    def loop_stop(self):
        """Stop background loop (for compatibility)"""
        pass
        
    def is_connected(self):
        """Check if connected"""
        return self.connected


def create_embedded_client(client_id: str = None):
    """Create an embedded MQTT client"""
    return EmbeddedMQTTClient(client_id)


if __name__ == "__main__":
    # Test the embedded broker
    print("🧪 Testing Embedded MQTT Broker")
    
    # Create broker
    broker = EmbeddedMQTTBroker()
    broker.start()
    
    # Create test clients
    def test_callback(topic, payload):
        print(f"📨 Received: {topic} = {payload}")
        
    # Test pub/sub
    broker.subscribe("test/topic", test_callback)
    broker.publish("test/topic", "Hello World!")
    
    time.sleep(1)
    broker.stop()
    print("✅ Test completed")
