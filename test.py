import logging
import socket
import sys
import ssl

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
hw3_logger = logging.getLogger('cs450-hw3')


def parse_url(url, scheme):
    """
    Parse the url for host, path, & port
    """
    port = -1
    if(len(url) == 1):
        #parsed = url[0].split('/', 1)
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
    
    if port == -1:
        parsed = host_name.split(":")
        host_name = parsed[0]
        port = int(parsed[1])
    
    full_list = [host_name, path, port]
	
    return full_list

def get_body_chunked(body_start):
    """
    Parses an HTTP Body formatted in the chunked transfer-encoding
    """
    chunkedData = b""
    
    while True:
		# Split at first CRLF
        partitions = body_start.split(b"\r\n", 1)
		# Get the size of chunk in hex
        sizeHex = partitions[0]

		# If it's 0, we reached end of response
        if sizeHex == b'0':
            break
        sizeInt = int(sizeHex, 16)

		# Now we take everything after the split
        chunk = partitions[1]
		# Only consider the data within the given size of chunk
        chunkedData += chunk[:sizeInt]
		# Update the data to parse the rest of the chunks
        body_start = chunk[sizeInt+2:]
    
    return chunkedData

def retrieve_url(url):
    """
    Parse the url
    """
    path_list = []
    url_length = len(url)

    """
    Determine the scheme of http or https
    """
    if url.find("http://", 0, 7) != -1:
        scheme = 'http'
        path_list = (url[7:url_length].split("/", 1))
    elif url.find("https://", 0, 8) != -1:
        scheme = 'https'
        path_list = (url[8:url_length].split("/",1))
    
    client_path = parse_url(path_list, scheme)

    """
    Connect to the host & port to get path
    """
    for res in socket.getaddrinfo(client_path[0], client_path[2], socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
        af, socktype, proto, canonname, sa = res
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

    client_request = ("GET " + client_path[1] + " HTTP/1.1\r\nHost:" + client_path[0] + "\r\nConnection: close\r\n\r\n")
    clientSocket.send(client_request.encode())
    data = clientSocket.recv(4096)

    # check if its not a 404 page
    if data.find(b"200 OK") == -1:
        return None
    
    # check for chunking encoding
    chunk = True
    if data.find(b"Transfer-Encoding: chunked\r\n") == -1:
        chunk = False
	
    # iterate thru the data to send
    newData = data
    while True:
        data = clientSocket.recv(4096)
        if not data:
            break
        newData += data

    parsed = newData.split(b"\r\n\r\n",2)
    finalData = parsed[1]

    # Chunk encoding
    if chunk == True:
        return get_body_chunked(finalData)

    return finalData


url = 'https://www.cs.uic.edu/~ckanich/'
print(retrieve_url(url))