import socket
import threading
from queue import Queue

host = '192.168.1.4'
port = 8001

request_queue = Queue()

backend_server =[
    ('127.0.0.1',8004),
    ('127.0.0.1',8005),
    ('127.0.0.1',8006)
]


def listen_active_conn():
    print("listening for active connections on: "+str(host)+":"+str(port))
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host,port))
    server.listen()
    while True:
        client,addr = server.accept()
        print("received connection from: "+str(addr))
        request_queue.put((client,addr))

def resolve_reqeust(conn,req,count):
    backend = socket.socket()
    print("connecting to backend server: "+str(backend_server[count]))
    backend.connect(backend_server[count])
    print("sending request to backend server: "+str(backend_server[count]))
    backend.sendall(req.encode())
    print("waiting for response from backend server: "+str(backend_server[count]))
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
    print("waiting for client request from: "+str(conn.getpeername()))
    req = conn.recv(1024).decode()
    print("received request from client: "+req)
    print("resolving request from client: "+str(conn.getpeername())+" to backend server: "+str(backend_server[count]))
    response = resolve_reqeust(conn,req,count)
    print("sending response to client: "+str(conn.getpeername()))
    conn.sendall(response)
    print("closing connection with client: "+str(conn.getpeername()))
    conn.close()

def solve():
    count = 0
    while True:
        if not request_queue.empty():
            print("active connections in queue: "+str(request_queue.qsize()))
            client, addr = request_queue.get()
            count = count%3
            request_handler(client,count)
            count = count+1
        else:
            continue


thread1 = threading.Thread(target=listen_active_conn)
thread1.start()

thread2 = threading.Thread(target=solve)
thread2.start()


# connect()