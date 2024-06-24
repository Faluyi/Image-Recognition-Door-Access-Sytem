import socket
import threading
import json
import bcrypt
import datetime
import logging
from pymongo.errors import DuplicateKeyError
from db.dbModels import UsersDb, logsDb
from concurrent.futures import ThreadPoolExecutor
from cryptography.fernet import Fernet, MultiFernet

logging.basicConfig(filename='server_errors.log', 
                    level=logging.ERROR,
                    format='%(asctime)s %(levelname)s:%(message)s')

Users = UsersDb()
Logs = logsDb()

key1 = b'q_liNo3weVdsXduBUYcNg1NrZ_koMQ0Sz7cbQGyax3A='
key2 = b'WKzylsCkB5e4dm5JDBYzwQyYlQ8Ha5EhOsbuXgO6IXI='
cipher = MultiFernet([Fernet(key1), Fernet(key2)])

class User:
    @staticmethod
    def register_user(username, password):
        try:
            user = {
                "username": username,
                "password": bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            }
            Users.add_user(user)
            return {
                "success": True,
                "response": "User registration successful"
            }
        except DuplicateKeyError:
            return {
                "success": False,
                "response": "User already exists"
            }
        except Exception as e:
            logging.error(f"Exception during registration: {e}")
            return {
                "success": False,
                "response": "Server error"
            }

    @staticmethod
    def authenticate_user(username, password):
        try:
            user = Users.get_user_by_username(username)
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                return {
                    "success": True,
                    "response": "Login successful"
                }
            else:
                return {
                    "success": False,
                    "response": "Login failed: Invalid credentials"
                }
        except Exception as e:
            logging.error(f"Exception during authentication: {e}")
            return {
                "success": False,
                "response": "User not found"
            }

class Log:
    @staticmethod
    def add_log(log):
        try:
            Logs.add_log(log)
            return {
                "success": True,
                "response": "Log added"
            }
        except Exception as e:
            logging.error(f"Exception during logging: {e}")
            return {
                "success": False,
                "response": "Server error"
            }

class ConnectionHandler:
    def handle_client(self, client_socket):
        while True:
            try:
                encrypted_data = client_socket.recv(4096)
                if not encrypted_data:
                    break

                decrypted_data = cipher.decrypt(encrypted_data).decode('utf-8')
                data_dict = json.loads(decrypted_data)
                command = data_dict.get('command')
                payload = data_dict.get('payload')

                if command == 'REGISTER':
                    username = payload.get('username')
                    password = payload.get('password')
                    response = User.register_user(username, password)["response"]

                elif command == 'LOGIN':
                    username = payload.get('username')
                    password = payload.get('password')
                    authenticated = User.authenticate_user(username, password)
                    response = authenticated["response"]
                    
                    if authenticated["success"]:
                        log = {
                            "username": username,
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        Log.add_log(log)
                
                elif command == 'LOG':
                    username = payload.get('username')
                    door = payload.get('door')
                    log = {
                        "username": username,
                        "door": door,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    Log.add_log(log)
                    response = "Log added successfully"
                    
                else:
                    response = "Invalid command"
                    
                encrypted_response = cipher.encrypt(response.encode('utf-8'))
                client_socket.sendall(encrypted_response)
            except Exception as e:
                logging.error(f"Exception: {e}")
                break

        client_socket.close()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', 5000))
        server_socket.listen(5)
        print("Server is listening for incoming connections...")

        with ThreadPoolExecutor(max_workers=10) as executor: 
            while True:
                client_socket, client_address = server_socket.accept()
                print(f"Connection from {client_address} has been established.")
                executor.submit(self.handle_client, client_socket)

if __name__ == "__main__":
    ConnectionHandler().start_server()
