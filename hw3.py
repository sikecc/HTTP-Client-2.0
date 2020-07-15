import logging
import socket
import sys
import ssl

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
hw3_logger = logging.getLogger('cs450-hw3')

"""
I used the code from the previous assignment to help me with this assignment
"""

def parse_url(url, scheme):
    """
    Parse the url for host, path, & port
    """
    # Set the port to false
    port = -1

    # Begin the parsing of the url
    if(len(url) == 1):
        path = "/"
    else:
        parsed = url[1].split('/', 1)
        path = "/" + parsed[0]
    
    host_name = url[0]
        
	# set port number to default
    if scheme == 'http':
        if host_name.find(":") == -1:
            port = 80
    elif scheme == 'https':
        if host_name.find(":") == -1:
            port = 443
    # set the port number to the found in the url
    if port == -1:
        parsed = host_name.split(":")
        host_name = parsed[0]
        port = int(parsed[1])
    
    full_list = [host_name, path, port]
	
    # return the list of url components
    return full_list

def get_body_chunked(body_start):
    """
    Parses an HTTP Body formatted in the chunked transfer-encoding, professor algorithm
    """
    chunkData = b""
    
    while True:
        # Spilt the response
        part = body_start.split(b"\r\n", 1)
        # Get the size
        size = part[0]
		
        # Break once the data has reached 0
        if size == b'0':
            break
        intSize= int(size, 16)

		# Take everything and sppilt
        chunked = part[1]
        chunkData += chunked[:intSize]
		# Update the data to parse the rest of the chunks
        body_start = chunked[intSize+2:]
    
    return chunkData

def send_req(s, req):
    s.sendall(req.encode())
    data = s.recv(4096)

    # check if its not a 404 page
    if data.find(b"200 OK") == -1:
        return None, False
    
    # check for chunking encoding
    if data.find(b"Transfer-Encoding: chunked\r\n") == -1:
        chunk = False
    else:
        chunk = True
	
    # Recieve data
    theData = data
    while True:
        data = s.recv(4096)
        if not data:
            break
        theData += data

    parsed = theData.split(b"\r\n\r\n",2)
    finalData = parsed[1]

    return finalData, chunk

def retrieve_url(url):
    # Parse the url
    path_list = []
    url_length = len(url)

    # Determine the scheme of http or https
    if url.find("http://", 0, 7) != -1:
        scheme = 'http'
        path_list = (url[7:url_length].split("/", 1))
    elif url.find("https://", 0, 8) != -1:
        scheme = 'https'
        path_list = (url[8:url_length].split("/",1))
    
    client_path = parse_url(path_list, scheme)

    # Connect to the host & port to get path
    for re in socket.getaddrinfo(client_path[0], client_path[2], socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
        af, socktype, proto, canonname, sa = re
        try:
            clientSocket = socket.socket(af, socktype, proto)
        except socket.error:
            clientSocket = None
            continue
        try:
            clientSocket.connect(sa)
        except socket.error:
            clientSocket.close()
            clientSocket = None
            continue
        break

    if clientSocket == None:
        hw3_logger.warning('Unable to open connection to: ({}, {})'.format(
            client_path[0], client_path[2]))
        return None
    hw3_logger.info('Opened connection to: ({}, {})'.format(client_path[0], client_path[2]))
    
    # Use SSL if requested
    if scheme == 'https':
        clientSocket = ssl.wrap_socket(clientSocket, cert_reqs=ssl.CERT_REQUIRED, ca_certs="cacerts.txt")

    # generate client request
    clientRequest = "GET {} HTTP/1.1\r\nHost: {}:{}\r\nConnection: Close\r\n\r\n"
    clientRequest = clientRequest.format(client_path[1], client_path[0], client_path[2])
    
    # Send the request and check if Transfer encoding = true
    finalData, chunk = send_req(clientSocket, clientRequest)
    clientSocket.close()
    
    # Chunk encoding
    if chunk == True:
        return get_body_chunked(finalData)

    
    return finalData

