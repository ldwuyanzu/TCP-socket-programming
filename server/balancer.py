#load balancer for assignment 4


import socket
import os
import datetime
import argparse
import threading
from serverd import *
import time

#create list of server using thread
#each server will have 2 state: waiting and responding
class balancerServer(threading.Thread):
    def __init__(self,port=8080):
        threading.Thread.__init__(self)
        self.RESPONDING=1
        self.WAITING=2
        self.STOP=0

        self.state=self.STOP
        self.STOPFLAG=False
        self.port=port
        self.host='0.0.0.0'
        self.portList=[]
        self.portListT=[]
#load balancer is a server itself with fixed port 8080 and at localhost
        self.newPort=8080
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.reques=None
        self.conn=None
#send response to client side   
    def send_response_to_client(self,sock, code, file_name):           
        #according to http code in different cases, generate response header
        self.newPort=self.getPort()
        date = datetime.datetime.now()            
        #show time now on responde msg
        date_string = 'Date: ' + date.strftime('%a, %d %b %Y %H:%M:%S EDT')
        message = 'HTTP/1.1 '
        if self.newPort==-1:
            message = message + '404' + ' Not Found\r\n' + date_string + '\r\n'
        elif code=='301':
            message=message+code+' 301 Moved Permanently\r\n'+date_string +'\r\n'   
        type = 'text/html'

        if(self.newPort!=-1):
            file_size = 0
            #header that return to client
            header = message + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size) 
            header=header+ '\r\nLocation: http://127.0.0.1:'+str(self.newPort)+file_name+'\r\n\r\n'
            try:
                sock.send(header.encode())
            except BaseException:
                return   
        else:
            file_size = os.path.getsize('./src/404.html')
            header = message + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + '\r\n\r\n'
            try:
                sock.send(header.encode())
            except BaseException:
                return    
            with open('./src/404.html', 'rb') as file_to_send:
                while True:
                    chunk = file_to_send.read(1024)
                    if chunk:
                        try:
                            sock.send(chunk)
                        except BaseException:
                            return 
                    else:
                        break
    def get_line_from_socket(self,sock):   #Retrieve client request header char by char, save in line
        done = False
        line = ''
        while (not done):
            char = sock.recv(1).decode()
            if (char == '\r'):
                pass
            elif (char == '\n'):
                done = True
            else:
                line = line + char
        return line
    def respond(self):     #read request, check if is valid request
        if self.request[0] != 'GET':
            print('balancer_server:'+str(self.port)+'->Invalid type of request received ... responding with error!')
            self.send_response_to_client(self.conn, '501', '501.html')
        elif self.request[2] != 'HTTP/1.1':
            print('balancer_server:'+str(self.port)+'->Invalid HTTP version received ... responding with error!')
            self.send_response_to_client(self.conn, '505', '505.html')
        #if not problem with request, redirect it
        else:
            file_name = self.request[1]
            self.send_response_to_client(self.conn, '301', file_name)
            print('balancer_server: redirection: '+str(self.port)+'->'+str(self.newPort))
        self.conn.close()    
    def acceptRequest(self):            
        self.conn, addr = self.server_socket.accept()
        self.request = self.get_line_from_socket(self.conn)
        self.request=self.request.split()
        # print(self.request)
        while (self.get_line_from_socket(self.conn) != ''): #get rid of noise in request
            pass   
    #get the fastest waiting server
    def getPort(self):
        if(len(self.portList)<=0):
            return -1
        if len(self.portListT)<=0:
            self.portListT=self.portList
        tempList=[]
        port=-1
        flag=False
        for i in self.portListT:
            if(i.state==i.WAITING and flag==False):
                port=i.port
                flag=True
                continue
            tempList.append(i)
        if(port==-1):
            self.portListT=self.portList
            tempList=[]
            port=-1
            flag=False
            for i in self.portListT:
                if(i.state==i.WAITING and flag==False):
                    port=i.port
                    flag=True
                    continue
                tempList.append(i)
        self.portListT=tempList
        return port       
#run this function when program was executed
    def run(self):
        
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print('Listening on port %s ...' % self.port)
        #find a waiting server
        while(self.STOPFLAG==False):
            self.state=self.WAITING
            self.acceptRequest()
            #set state to responding server
            self.state=self.RESPONDING
            self.respond()
        self.STOPFLAG=False
        self.state=self.STOP
    def stop(self):
        self.STOPFLAG=True

def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n' 
    return request
#test server performance
def testDelay(bal,port):
    delay=0
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(10)
    time_now=time.time()
    try:
        client_socket.connect(('localhost', port))
    #return a huge number if something went wrong
    except ConnectionRefusedError:
        # print("Sdfsdf")
        return 10*1000000

    message = prepare_get_message('localhost', port, '/test.htm')
    client_socket.send(message.encode())
    headers_done = False
    # if response_list[1] != '200':
    #     # print('Error:  An error response was received from the server.  Details:\n')
    #     # print(response_line);
    bytes_to_read = 0
    while (not headers_done):
        try:
            header_line = bal.get_line_from_socket(client_socket)
        except BaseException:
            return 10*1000000

        header_list = header_line.split(' ')
        if (header_line == ''):
            headers_done = True
        elif (header_list[0] == 'Content-Length:'):
            bytes_to_read = int(header_list[1])
    bytes_read=0
    while (bytes_read < bytes_to_read):
        try:
            chunk = client_socket.recv(1024)
        
        except BaseException:
            return 10*1000000
        if(len(chunk)<=0):
            return 10*1000000
        bytes_read += len(chunk)
    time_end=time.time()
    delay=time_end-time_now
    return delay*1000000
#sort server performance by speed, list them form the fastest
def sort_all(serverList,bal):
    portList=[]
    for i in serverList:
        if i.state==i.WAITING:
            i.acceptDelay=testDelay(bal,i.port)
            portList.append(i)
            time.sleep(0.5)

    if len(portList)<=0:
        time.sleep(10)
        return
    else:    
        portList=sorted(portList, key=lambda s: s.acceptDelay)
        bal.portList=portList
    #print out test result
    print("Server Performance:---------",flush=True)    
    
    for i in portList:
        print('port: '+str(i.port)+'->'+str(round(i.acceptDelay,4))+' \tus',flush=True) 
          
def balancer():
    #balancer server fixed at port 8080
    bal=balancerServer(8080)
    #initiate list of servers
    serverList=[]
    serverList.append(ServerTest(1121))
    serverList.append(ServerTest(1122))
    serverList.append(ServerTest(1123))
    serverList.append(ServerTest(1124))
    serverList.append(ServerTest(1125))
    serverList.append(ServerTest(1126))
    serverList.append(ServerTest(1127))
    serverList.append(ServerTest(1128))
    serverList.append(ServerTest(1130))
    serverList.append(ServerTest(1131))
    serverList.append(ServerTest(1132))

    for i in serverList:
        i.start()

    bal.start()

    while(True):
        
        sort_all(serverList,bal)
        #set time for revaluate, 1 minute here
        time.sleep(60)
if __name__ == '__main__':        
    balancer()
# d=balancerServer(5678)
# d.start()
# a=ServerTest(8080)
# a.start()
# b=ServerTest(1234)
# b.start()
# c=ServerTest(4567)
# c.start()
# while(1):
#     print(d.state)
#     time.sleep(0.5)

