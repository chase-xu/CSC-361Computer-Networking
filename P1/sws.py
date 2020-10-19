from socket import *
import sys
from threading import Thread
from datetime import datetime
import re


#/sbin/ifconfig
#10.10.1.100
#nc h2 80
        
def serve(ip, port_num):
    serverPort = int(port_num)
    serverIP = ip
    serverSocket = socket(AF_INET,SOCK_STREAM)
    serverSocket.bind((serverIP,serverPort)) 
    threads = []
    
    while True:
        serverSocket.listen()
        print ("Waiting for incoming connections...")
        conn, addr = serverSocket.accept()
        print ('Got connection from ', addr)
        t_thread =Thread(target = process_cmd ,args=(conn, addr, ip, serverPort))
        t_thread.start()
        threads.append(t_thread)

    for t in threads:
        t.join()
    print ('The server is ready to receive')
        
def process_cmd(connectionSocket, addr, ip, port):
    now = datetime.now().time()
    http = None
    f = None
    requests = None
    responds = None
    state = None
    cmd = None
    while True:
        sentence = ""
        connectionSocket.settimeout(25)
        try:
            sentence = connectionSocket.recv(1024).decode(encoding='UTF-8',errors='strict')                
        except:
            connectionSocket.send(b'\nTime Out\n')
            break
        connectionSocket.settimeout(None)
        requests = sentence.split(' ')
        while '' in requests: requests.remove('')
        
        #Process requests
        if requests[0] == "GET":
            file = None
            try:
                file = requests[1].strip('/')
                http = requests[2].strip('\n').upper()
                cmd = requests[0] +' '+ file + ' ' + http

            except:
                connectionSocket.send(b'400 Bad Request\n')
                print(f"{now}: {addr[0]}:{addr[1]} {cmd};400 Bad Request" )
                break
            
            match = re.compile('(HTTP|http)/\d+(\.\d*)?')
            if match.fullmatch(http) == None:
                connectionSocket.send(b'400 Bad Request\n')
                print(f"{now}: {addr[0]}:{addr[1]} {cmd};400 Bad Request" )
                break

            try:
                f = open(file,'rb')
            except FileNotFoundError:
                responds = http+ ' 404 Not Found'
                connectionSocket.send(responds.encode('utf-8')) 
                connectionSocket.send(b'\n') 
                print(f"{now}: {addr[0]}:{addr[1]} {cmd};{responds}" )
                if state == "KEEP-ALIVE":
                    connectionSocket.send(b'Connection: '+ state.encode('utf-8')+b'\n')
                    continue
                break
            responds = http + " 200 OK"
            continue
        elif requests[0].upper().strip() == "CONNECTION:" or requests[0].upper().strip() == 'CONNECTION':
            check_state = 0
            if requests[0].upper().strip() == 'CONNECTION':
                if requests[1].strip() != ":":
                    connectionSocket.send(b'400 Bad Request\n')
                    print(f"{now}: {addr[0]}:{addr[1]} {cmd};400 Bad Request" )                    
                    break                    
                check_state = 1
            if requests[1+check_state].upper().strip('\n') == "KEEP-ALIVE":
                if http == None or f == None:
                    connectionSocket.send(b'400 Bad Request\n')
                    print(f"{now}: {addr[0]}:{addr[1]} {cmd};400 Bad Request" )                    
                    break
                state = "KEEP-ALIVE"
                responds = http+ " 200 OK"
                continue
            elif requests[1+check_state].upper().strip('\n') == "CLOSE":
                state = 'CLOSE'
                if f == None:
                    responds = '400 Bad Request'
                    connectionSocket.send(responds.encode('utf-8'))
                    print(f"{now}: {addr[0]}:{addr[1]} {cmd};400 Bad Request" )                    
                    break
                else:
                    responds = http+ " 200 OK"
                    continue
            else:
                responds = '400 Bad Request'
                connectionSocket.send(responds.encode('utf-8'))
                print(f"{now}: {addr[0]}:{addr[1]} {cmd};{responds}" )
                break
                
        elif requests[0] == '\n':
            if len(requests) == 1 and f == None:
                responds = http + ' 400 Bad Request'
                connectionSocket.send(responds.encode('utf-8'))
                print(f"{now}: {addr[0]}:{addr[1]} {cmd};{responds}" )
                break
            else:
                if f != None:
                    responds = http+ " 200 OK"
                    connectionSocket.send(responds.encode('utf-8') + b'\n')
                    l = f.read(1024)
                    while (l):
                        connectionSocket.send(l)
                        l = f.read(1024)
                    f.close()
                    connectionSocket.send(b'\n\nFile Sent, Thanks!\n \n')
                    connectionSocket.send(b"Connection: "+state.encode('utf-8')+b'\n')
                else:
                    responds = '400 Bad Request'
                    connectionSocket.send(responds.encode('utf-8'))
                if state == "KEEP-ALIVE":
                    print(f"{now}: {addr[0]}:{addr[1]} {cmd};{responds}")
                    http = None
                    f = None
                    continue
                elif state == "CLOSE":
                    print(f"{now}: {addr[0]}:{addr[1]} {cmd};{responds}")
                    break
                elif state == None:
                    connectionSocket.send(b'Missing Connection type. The connection will close after this operation.\n')
                    break
        else:
            if http == None:
                responds = '400 Bad Request'
            else:
                responds = http + ' 400 Bad Request'
            if cmd == None:
                cmd = sentence.strip('\n')
            connectionSocket.send(responds.encode('utf-8'))
            print(f"{now}: {addr[0]}:{addr[1]} {cmd};{responds}" )
            break
    
    connectionSocket.close()


if __name__ == "__main__":
    cmd = sys.argv
    serve(cmd[1], cmd[2])