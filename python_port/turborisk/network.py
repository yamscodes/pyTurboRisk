"""
TurboRisk - Network Multiplayer Support
Python port - Network module for multiplayer functionality

This module provides the foundation for network multiplayer support in TurboRisk.
Currently implements the basic structure and can be expanded for full multiplayer.
"""

import socket
import threading
import json
import queue
from enum import Enum
from typing import Optional, Dict, Any, Tuple

from .globals import G, MAXPLAYERS


# =============================================================================
# Network Message Types
# =============================================================================

class NetworkMessageType(Enum):
    """Types of network messages"""
    CONNECT = 1
    DISCONNECT = 2
    JOIN_GAME = 3
    LEAVE_GAME = 4
    GAME_START = 5
    GAME_STATE = 6
    PLAYER_MOVE = 7
    ATTACK = 8
    MOVE_ARMIES = 9
    END_TURN = 10
    CHAT = 11
    PING = 12
    PONG = 13
    ERROR = 14


# =============================================================================
# Network Message Class
# =============================================================================

class NetworkMessage:
    """Represents a network message"""
    
    def __init__(self, msg_type: NetworkMessageType, data: Dict[str, Any] = None):
        self.msg_type = msg_type
        self.data = data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'type': self.msg_type.value,
            'data': self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkMessage':
        """Create from dictionary"""
        msg_type = NetworkMessageType(data['type'])
        return cls(msg_type, data.get('data', {}))
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'NetworkMessage':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


# =============================================================================
# Network Player Class
# =============================================================================

class NetworkPlayer:
    """Represents a network player"""
    
    def __init__(self, player_id: int, name: str, address: Tuple[str, int]):
        self.player_id = player_id
        self.name = name
        self.address = address
        self.connected = True
        self.last_ping = 0
    
    def disconnect(self):
        """Mark player as disconnected"""
        self.connected = False


# =============================================================================
# Network Server Class
# =============================================================================

class NetworkServer:
    """Network server for hosting multiplayer games"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 1978):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.players: Dict[int, NetworkPlayer] = {}
        self.message_queue = queue.Queue()
        self.server_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the network server"""
        if self.running:
            return False
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(MAXPLAYERS)
            self.running = True
            
            self.server_thread = threading.Thread(target=self._run, daemon=True)
            self.server_thread.start()
            
            G.b_network_server = True
            return True
        except Exception as e:
            print(f"Failed to start network server: {e}")
            return False
    
    def stop(self):
        """Stop the network server"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        if self.server_thread:
            self.server_thread.join(timeout=5)
        G.b_network_server = False
    
    def _run(self):
        """Main server loop"""
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
            except:
                break
    
    def _handle_client(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle a connected client"""
        try:
            # Read player info
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                return
            
            msg = NetworkMessage.from_json(data)
            if msg.msg_type == NetworkMessageType.CONNECT:
                player_id = msg.data.get('player_id', 0)
                player_name = msg.data.get('name', 'Unknown')
                
                # Add player
                player = NetworkPlayer(player_id, player_name, address)
                self.players[player_id] = player
                
                # Send acknowledgment
                ack = NetworkMessage(NetworkMessageType.CONNECT, {
                    'player_id': player_id,
                    'status': 'accepted'
                })
                client_socket.sendall(ack.to_json().encode('utf-8'))
                
                # Queue message for game
                self.message_queue.put(msg)
                
                # Handle messages from this client
                while self.running:
                    data = client_socket.recv(4096).decode('utf-8')
                    if not data:
                        break
                    
                    msg = NetworkMessage.from_json(data)
                    self.message_queue.put(msg)
                    
                    # Send to all other players
                    self._broadcast(msg, exclude=player_id)
            
        except Exception as e:
            print(f"Client handler error: {e}")
        finally:
            client_socket.close()
    
    def _broadcast(self, msg: NetworkMessage, exclude: int = None):
        """Broadcast message to all connected players except one"""
        for player_id, player in self.players.items():
            if player_id != exclude and player.connected:
                # In a real implementation, we would send to the actual socket
                # For now, just queue the message
                self.message_queue.put(msg)
    
    def get_message(self) -> Optional[NetworkMessage]:
        """Get a message from the queue"""
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None


# =============================================================================
# Network Client Class
# =============================================================================

class NetworkClient:
    """Network client for connecting to multiplayer games"""
    
    def __init__(self, host: str = 'localhost', port: int = 1978):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.player_id = 0
        self.message_queue = queue.Queue()
        self.client_thread: Optional[threading.Thread] = None
    
    def connect(self, player_name: str) -> bool:
        """Connect to a network server"""
        if self.connected:
            return False
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            
            # Send connection message
            msg = NetworkMessage(NetworkMessageType.CONNECT, {
                'name': player_name
            })
            self.socket.sendall(msg.to_json().encode('utf-8'))
            
            # Wait for acknowledgment
            data = self.socket.recv(1024).decode('utf-8')
            if not data:
                return False
            
            ack = NetworkMessage.from_json(data)
            if ack.msg_type == NetworkMessageType.CONNECT:
                self.player_id = ack.data.get('player_id', 0)
                self.connected = True
                
                # Start message receiver thread
                self.client_thread = threading.Thread(target=self._receive, daemon=True)
                self.client_thread.start()
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        self.connected = False
        if self.socket:
            try:
                msg = NetworkMessage(NetworkMessageType.DISCONNECT)
                self.socket.sendall(msg.to_json().encode('utf-8'))
                self.socket.close()
            except:
                pass
        if self.client_thread:
            self.client_thread.join(timeout=5)
    
    def _receive(self):
        """Receive messages from the server"""
        while self.connected:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                msg = NetworkMessage.from_json(data)
                self.message_queue.put(msg)
                
            except:
                break
    
    def send(self, msg: NetworkMessage) -> bool:
        """Send a message to the server"""
        if not self.connected:
            return False
        
        try:
            self.socket.sendall(msg.to_json().encode('utf-8'))
            return True
        except:
            return False
    
    def get_message(self) -> Optional[NetworkMessage]:
        """Get a message from the queue"""
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None


# =============================================================================
# Network Game Manager
# =============================================================================

class NetworkGameManager:
    """Manages network multiplayer games"""
    
    def __init__(self):
        self.server = NetworkServer()
        self.client = NetworkClient()
        self.is_host = False
        self.connected = False
    
    def host_game(self, port: int = 1978) -> bool:
        """Host a multiplayer game"""
        self.is_host = True
        return self.server.start(port=port)
    
    def join_game(self, host: str, port: int, player_name: str) -> bool:
        """Join a multiplayer game"""
        self.is_host = False
        return self.client.connect(host=host, port=port, player_name=player_name)
    
    def leave_game(self):
        """Leave the current game"""
        if self.is_host:
            self.server.stop()
        else:
            self.client.disconnect()
        self.is_host = False
        self.connected = False
    
    def send_move(self, move_data: Dict[str, Any]) -> bool:
        """Send a game move to other players"""
        msg = NetworkMessage(NetworkMessageType.PLAYER_MOVE, move_data)
        if self.is_host:
            self.server._broadcast(msg)
            return True
        else:
            return self.client.send(msg)
    
    def send_attack(self, attack_data: Dict[str, Any]) -> bool:
        """Send an attack to other players"""
        msg = NetworkMessage(NetworkMessageType.ATTACK, attack_data)
        if self.is_host:
            self.server._broadcast(msg)
            return True
        else:
            return self.client.send(msg)
    
    def send_chat(self, message: str) -> bool:
        """Send a chat message to other players"""
        msg = NetworkMessage(NetworkMessageType.CHAT, {'message': message})
        if self.is_host:
            self.server._broadcast(msg)
            return True
        else:
            return self.client.send(msg)
    
    def get_message(self) -> Optional[NetworkMessage]:
        """Get a message from the network"""
        if self.is_host:
            return self.server.get_message()
        else:
            return self.client.get_message()
    
    def process_messages(self):
        """Process all pending network messages"""
        while True:
            msg = self.get_message()
            if msg is None:
                break
            
            # Handle different message types
            if msg.msg_type == NetworkMessageType.CHAT:
                print(f"Chat: {msg.data.get('message', '')}")
            elif msg.msg_type == NetworkMessageType.PLAYER_MOVE:
                print(f"Player move: {msg.data}")
            elif msg.msg_type == NetworkMessageType.ATTACK:
                print(f"Attack: {msg.data}")
            elif msg.msg_type == NetworkMessageType.GAME_STATE:
                print(f"Game state update: {msg.data}")
            elif msg.msg_type == NetworkMessageType.ERROR:
                print(f"Error: {msg.data.get('error', '')}")


# =============================================================================
# Utility Functions
# =============================================================================

def start_network_game(host: bool = True, port: int = 1978, player_name: str = "Player"):
    """
    Start a network game
    
    Args:
        host: If True, host a game. If False, join a game.
        port: Network port to use
        player_name: Player name
    
    Returns:
        NetworkGameManager instance
    """
    manager = NetworkGameManager()
    
    if host:
        if manager.host_game(port=port):
            print(f"Hosting game on port {port}")
            manager.connected = True
        else:
            print(f"Failed to host game on port {port}")
    else:
        if manager.join_game(host='localhost', port=port, player_name=player_name):
            print(f"Joined game as {player_name}")
            manager.connected = True
        else:
            print(f"Failed to join game")
    
    return manager


# Initialize global network state
G.b_network_server = False
G.b_network_client = False
G.network_manager = None
