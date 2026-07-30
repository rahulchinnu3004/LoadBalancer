import socket
import threading
import time
import logging
import json
from queue import Queue

host = '192.168.1.4'
port = 8001
backend_count = -1
rr_lock = threading.Lock()

request_queue = Queue()

backend_server =[
    ('127.0.0.1',8004),
    ('127.0.0.1',8005),
    ('127.0.0.1',8006)
]

backend_stats = {
    ("127.0.0.1", 8004): {
        "healthy": True,
        "requests": 0,
        "failures": 0,
        "last_checked": None
    },
    ("127.0.0.1", 8005): {
        "healthy": True,
        "requests": 0,
        "failures": 0,
        "last_checked": None
    },
    ("127.0.0.1", 8006): {
        "healthy": True,
        "requests": 0,
        "failures": 0,
        "last_checked": None
    }
}

healthy_servers = [True, True, True]


def listen_active_conn():
    logging.info(f"listening for active connections on: {host}:{port}")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host,port))
    server.listen()
    while True:
        client,addr = server.accept()
        logging.info(f"received connection from: {addr}")
        request_queue.put((client,addr))

def resolve_reqeust(conn,req,count):
    backend = socket.socket()
    logging.info(f"connecting to backend server: {backend_server[count]}")
    backend.connect(backend_server[count])
    logging.info(f"sending request to backend server: {backend_server[count]}")
    backend.sendall(req.encode())
    logging.info(f"waiting for response from backend server: {backend_server[count]}")
    backend_stats[backend_server[count]]["requests"] += 1
    header_data = b""

    while b"\r\n\r\n" not in header_data:
        header_data += backend.recv(1024)
    
    header, body = header_data.split(b"\r\n\r\n", 1)
    content_length = 0

    for line in header.decode().split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break

    while len(body) < content_length:
        body += backend.recv(4096)
    backend.close()
    
    return header + b"\r\n\r\n" + body

def request_handler(conn,count):
    logging.info(f"waiting for client request from: {conn.getpeername()}")
    req = conn.recv(1024).decode()
    get_request_endpoint = req.split(" ")[1]
    if get_request_endpoint == "/stats":
        response = statics_of_servers()
        logging.info(f"response of stats request from client: {conn.getpeername()} is: {response}")
        conn.sendall(response)
        conn.close()
        return
    else:
        logging.info(f"received request from client: {req}")
        logging.info(f"resolving request from client: {conn.getpeername()} to backend server: {backend_server[count]}")
        response = resolve_reqeust(conn,req,count)
        logging.info(f"sending response to client: {conn.getpeername()}")
        conn.sendall(response)
        logging.info(f"closing connection with client: {conn.getpeername()}")
        conn.close()

def get_healthy_server(last_index):
    n = len(backend_server)

    for _ in range(n):
        last_index = (last_index + 1) % n
        if healthy_servers[last_index]:
            return last_index
    return None


def solve():
    global backend_count
    while True:
        logging.info(f"active connections in queue: {request_queue.qsize()}")
        client, addr = request_queue.get()
        with rr_lock:
            backend_count = get_healthy_server(backend_count)
            selected_backend =backend_count
        request_handler(client,selected_backend)

def start_worker_threads(num_threads):
    for thread_id in range(num_threads):
        thread = threading.Thread(target=solve,name=f"WorkerThread-{thread_id}")
        thread.start()


def health_check():
    while True:
        for server in backend_server:
            try:
                backend = socket.socket()
                backend.connect(server)
                backend.sendall(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
                response = backend.recv(1024).decode()
                if "healthy" in response:
                    logging.info(f"Backend server {server} is healthy.")
                    healthy_servers[backend_server.index(server)] = True
                    backend_stats[server]["healthy"] = True
                    backend_stats[server]["last_checked"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                else:
                    logging.info(f"Backend server {server} is not healthy.")
                    healthy_servers[backend_server.index(server)] = False
                    backend_stats[server]["healthy"] = False
                    backend_stats[server]["last_checked"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                backend.close()
            except Exception as e:
                logging.error(f"Error checking health of backend server {server}: {e}")
                healthy_servers[backend_server.index(server)] = False
                backend_stats[server]["healthy"] = False
                backend_stats[server]["last_checked"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        time.sleep(5)


def statics_of_servers():
    logging.info("Fetching statistics of backend servers.")
    body = {
        f"{ip}:{port}": data
        for (ip, port), data in backend_stats.items()
    }
    body = json.dumps(body, indent=4).encode()
    logging.info(f"Statistics of backend servers: {body.decode()}")
    response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/json\r\n"
        + f"Content-Length: {len(body)}\r\n".encode()
        + b"Connection: close\r\n"
        + b"\r\n"
        + body
    )
    logging.info(f"Response to be sent for /stats request: {response.decode()}")
    return response

def main():

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',handlers=[logging.FileHandler("load-balancer.log"), logging.StreamHandler()])
    thread1 = threading.Thread(target=listen_active_conn,name="ListenerThread")
    thread1.start()

    start_worker_threads(4)

    thread3 = threading.Thread(target=health_check,name="HealthCheckThread")
    thread3.start()

main()