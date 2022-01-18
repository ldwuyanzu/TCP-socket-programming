import socket
import os
import datetime
import argparse
import threading
class ServerTest(threading.Thread):
    def __init__(self,port=8080):
        threading.Thread.__init__(self)
        self.RESPONDING=1
        self.WAITING=2
        self.STOP=0
        
        self.state=self.STOP
        self.STOPFLAG=False
        self.port=port
        self.host='0.0.0.0'

        self.acceptDelay=0
        self.BUFFER_SIZE=1024


        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.reques=None
        self.conn=None
    def send_response_to_client(self,sock, code, file_name): 
   
        date = datetime.datetime.now()            
        date_string = 'Date: ' + date.strftime('%a, %d %b %Y %H:%M:%S EDT')
        message = 'HTTP/1.1 '
        if code== '200':
            message = message + code + ' OK\r\n' + date_string + '\r\n'
        elif code == '404':
            message = message + code + ' Not Found\r\n' + date_string + '\r\n'
        elif code == '501':
            message = message + code + ' Method Not Implemented\r\n' + date_string + '\r\n'
        elif code == '505':
            message = message + code + ' Version Not Supported\r\n' + date_string + '\r\n'
        elif code == '304':
            message = message + code + ' 304 Not Modified result\r\n' + date_string + '\r\n'

        if ((file_name.endswith('.jpg')) or (file_name.endswith('.jpeg'))):
            type = 'image/jpeg'
        elif (file_name.endswith('.gif')):
            type = 'image/gif'
        elif (file_name.endswith('.png')):
            type = 'image/jpegpng'
        elif ((file_name.endswith('.html')) or (file_name.endswith('.htm'))):
            type = 'text/html'
        else:
            type = 'application/octet-stream'

        file_size = os.path.getsize(file_name)
        header = message + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + '\r\n\r\n'
        try:
            sock.send(header.encode())
        except BaseException:
            return 


        with open(file_name, 'rb') as file_to_send:
            while True:
                chunk = file_to_send.read(self.BUFFER_SIZE)
                if chunk:
                    try:
                        sock.send(chunk)
                    except BaseException:
                        return 
                else:
                    break
    def get_line_from_socket(self,sock): 
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
    def respond(self):
        # print(self.request)
        if self.request[0] != 'GET':
            # print('port:'+str(self.port)+'->Invalid type of request received ... responding with error!')
            self.send_response_to_client(self.conn, '501', '501.html')
        elif self.request[2] != 'HTTP/1.1':
            # print('port:'+str(self.port)+'->Invalid HTTP version received ... responding with error!')
            self.send_response_to_client(self.conn, '505', '505.html')
        elif len(self.request[1])>1 and self.request[1][0]=='/':
            file_name = self.request[1]
            while (file_name[0]== '/'):
                file_name = file_name[1:]
            file_name=os.path.join('src',file_name)

            if (not os.path.exists(file_name)):
                # print('port:'+str(self.port)+'->Requested file does not exist ... responding with error!')
                self.send_response_to_client(self.conn, '404', './src/404.html')

            else:
                # print('port:'+str(self.port)+'->Requested file good to go!  Sending file ...')
                self.send_response_to_client(self.conn, '200', file_name)
        else: 
            # print('port:'+str(self.port)+'->Requested file does not exist ... responding with error!')
            self.send_response_to_client(self.conn, '404', './src/404.html')   
        self.conn.close()   
    def acceptRequest(self):            
        self.conn, addr = self.server_socket.accept()
        self.request = self.get_line_from_socket(self.conn)
        self.request=self.request.split()
        while (self.get_line_from_socket(self.conn) != ''): 
            pass   
    def run(self):
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print('Listening on port %s ...' % self.port)
        while(self.STOPFLAG==False):
            self.state=self.WAITING
            self.acceptRequest()
            self.state=self.RESPONDING
            self.respond()
        self.STOPFLAG=False
        self.state=self.STOP
    def stop(self):
        self.STOPFLAG=True
