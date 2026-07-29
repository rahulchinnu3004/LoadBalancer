import socket

host = '192.168.1.4'
port = 8001

def conn():
    server = socket.socket()
    # server.bind((host,port))
    server.connect((host,port))
    message = (
    "GET / HTTP/1.1\r\n"
    "Host: localhost:8001\r\n"
    "\r\n"
    )

    server.sendall(message.encode())
    data = server.recv(1024).decode()
    print("Received from the server: "+data)

    # while True:
    #     data = server.recv(1024).decode()
    #     if data == "exit":
    #         break
    #     print("Recieved from the server:"+data)
    #     # message = "executed " + data
    #     message = input("victim :")
    #     server.send(message.encode())


conn()