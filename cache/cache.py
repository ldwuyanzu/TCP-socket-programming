# cache.py

from urllib.parse import urlparse, urljoin
import argparse
import socket
import os
import datetime
import signal
import sys
import argparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen

# Constant for our buffer size
BUFFER_SIZE = 1024

def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n' 
    return request


# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):

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

# Read a file from the socket and print it out.  (For errors primarily.)

def print_file_from_socket(sock, bytes_to_read):

    bytes_read = 0
    while (bytes_read < bytes_to_read):
        chunk = sock.recv(BUFFER_SIZE)
        bytes_read += len(chunk)
        print(chunk.decode())

# Read a file from the socket and save it out.

def save_file_from_socket(sock, bytes_to_read, file_name):

    with open(file_name, 'wb') as file_to_write:
        bytes_read = 0
        while (bytes_read < bytes_to_read):
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)

# Signal handler for graceful exiting.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)

# Creating an HTTP response

def prepare_response_message(value):
    date = datetime.datetime.now()
    date_string = 'Date: ' + date.strftime('%a, %d %b %Y %H:%M:%S EDT')
    message = 'HTTP/1.1 '
    if value == '200':
        message = message + value + ' OK\r\n' + date_string + '\r\n'
    elif value == '404':
        message = message + value + ' Not Found\r\n' + date_string + '\r\n'
    elif value == '501':
        message = message + value + ' Method Not Implemented\r\n' + date_string + '\r\n'
    elif value == '505':
        message = message + value + ' Version Not Supported\r\n' + date_string + '\r\n'
    elif value == '304':
        message = message + value + ' 304 Not Modified result\r\n' + date_string + '\r\n'
    return message

# Send the given response and file back to the client.
def send_response_to_client(sock, code, file_name):

    # Determinng the extention and type of file to be used.

    if ((file_name.endswith('.jpg')) or (file_name.endswith('.jpeg'))):
        type = 'image/jpeg'
    elif ((file_name.endswith('.html')) or (file_name.endswith('.htm'))):
        type = 'text/html'
    
    # Get size of file

    file_size = os.path.getsize(file_name)

    # Construct header and send it
    header = prepare_response_message(code) + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + '\r\n\r\n'
    sock.send(header.encode())

    # Open the file, read it, and send it

    with open(file_name, 'rb') as file_to_send:
        while True:
            chunk = file_to_send.read(BUFFER_SIZE)
            if chunk:
                sock.send(chunk)
            else:
                break
# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):

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

def webcache():
    #Initializing the Get port command line argument
    parser = argparse.ArgumentParser()
    parser.add_argument('port')
    args = parser.parse_args()

    # Defining the socket host and the port
    SERVER_HOST = '0.0.0.0'
    SERVER_PORT = int(args.port)

    # Initialize socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))

    server_socket.listen(1)

    print('The Webcache is listening on port %s ...' % SERVER_PORT)
    
    while (1):
        print('Waiting for incoming client connection ...')
        conn, addr = server_socket.accept()
        print('Accepted connection from client address:', addr)
        print('Connection to client established, waiting to receive message...')

        # Obtaining the request from the socket. Looking at the request and
        # figure out what to do based on the contents of things.

        request = get_line_from_socket(conn)
        print('Received request:  ' + request)
        request_list = request.split()

        # This server doesn't care about headers, so we just clean them up.

        while (get_line_from_socket(conn) != ''):
            pass

        # If we did not get a GET command respond with a 501.

        if request_list[0] != 'GET':
            print('Invalid type of request received ... responding with error!')
            send_response_to_client(conn, '501', '501.html')

        # If we did not get the proper HTTP version respond with a 505.

        elif request_list[2] != 'HTTP/1.1':
            print('Invalid HTTP version received ... responding with error!')
            send_response_to_client(conn, '505', '505.html')

        # We have the right request and version, so check if file exists.
                  
        else:

            # If requested file begins with a / we strip it off.

            file_name = request_list[1]
            while (file_name[0] == '/'):
                file_name = file_name[1:]

        if (not os.path.exists(file_name)):
                print('Requested file does not exist ... feching from server!')
                fetch_from_server(file_name)
            # File exists on the main server, so prepare to send it!  
        else:
            print('File Found on Cache!  Sending file ...')
            send_response_to_client(conn, '200', file_name)

   

            print('Connecting to server ...')


def fetch_from_server(file_name):
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL to fetch with an HTTP GET request")
    args = parser.parse_args()

    # Check the URL passed in and make sure it's valid.  If so, keep track of
    # things for later.

    try:
        parsed_url = 'http://localhost:8000/'+file_name
        host = "localhost"
        port = 8000
        file_name = file_name
    except ValueError:
        sys.exit(1)
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
    except ConnectionRefusedError:
        print('Error: Host / Port are not accepting connections.')
        sys.exit(1)

    # Successful Connection, send msg
   
    print('Connection to server established. Sending message...\n')
    message = prepare_get_message(host, port, file_name)
    client_socket.send(message.encode())
   
    # Receive the response from the main server and start taking a look at it

    response_line = get_line_from_socket(client_socket)
    response_list = response_line.split(' ')
    headers_done = False
        
    # If server is not 200(not ok), dump everything
    
    if response_list[1] != '200':
        print('Error:  An error response was received from the server.  Details:\n')
        print(response_line);
        bytes_to_read = 0
        while (not headers_done):
            header_line = get_line_from_socket(client_socket)
            print(header_line)
            header_list = header_line.split(' ')
            if (header_line == ''):
                headers_done = True
            elif (header_list[0] == 'Content-Length:'):
                bytes_to_read = int(header_list[1])
        print_file_from_socket(client_socket, bytes_to_read)
        sys.exit(1)
           
    
    # If it's OK, then retrieve and write the file out.

    else:

        print('Server sending file and saving on cache')

        # If requested file begins with a / we strip it off.
       
        while (file_name[0] == '/'):
            file_name = file_name[1:]

        # Go through headers,find and save size of it.
   
        bytes_to_read = 0
        while (not headers_done):
            header_line = get_line_from_socket(client_socket)
            header_list = header_line.split(' ')
            if (header_line == ''):
                headers_done = True
            elif (header_list[0] == 'Content-Length:'):
                bytes_to_read = int(header_list[1])
        save_file_from_socket(client_socket, bytes_to_read, file_name) 
   

if __name__ == '__main__':
    webcache()
