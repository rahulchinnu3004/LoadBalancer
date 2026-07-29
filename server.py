import socket
import threading

host = '192.168.1.4'
port = 8001

active_conn = []
backend_server =[
    ('127.0.0.1',8004),
    ('127.0.0.1',8005),
    ('127.0.0.1',8006)
]
def listen_active_conn():
    print("Started listening for active connections..")
    add_to_active_conn()

def add_to_active_conn():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host,port))
    server.listen()
    while True:
        client,addr = server.accept()
        active_conn.append((client,addr))
        print("adding to active conn: "+str(addr))


def resolve_reqeust(conn,count):
    req = conn.recv(1024).decode()
    backend = socket.socket()
    backend.connect(backend_server[count])
    backend.sendall(req.encode())
    resp = backend.recv(1024).decode()
    conn.sendall(resp.encode())

def solve():
    count = 0
    while True:
        for i in active_conn:
            count = count%3
            resolve_reqeust(i[0],count)
            count = count+1
            active_conn.pop(0)

thread1 = threading.Thread(target=listen_active_conn)
thread1.start()

thread2 = threading.Thread(target=solve)
thread2.start()


# connect()