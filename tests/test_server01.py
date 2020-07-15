#!/usr/bin/env python3

import argparse
import socket
import sys
import time

"""Test Case Write-up:

Behavior:
    This test case generates a normal HTTP response, which includes headers
    that are not testing for any edge cases and a simple static body whose
    length is correctly specified with a Content-Length.  However, the abnormal
    thing about this server is that it deliberately sends the response one byte
    at a time via calls to sendall and sleeps for 10ms (0.01s) in between each
    call.  As confirmed via wireshark, this in practice leads to many
    individual 1-byte TCP packets being generated.

Tests:
    This test is designed to verify that the HTTP client correctly handles
    partial data being returned by the 'recv' system call.  If the client does
    not handle partial recvs, then it will likely think that this response is
    not compliant with the HTTP protocol, when in fact it is.

Notes:
    This test case takes longer to run than other test cases because it uses
    time.sleep(0.01) to delay the responses.
"""

def get_test_response():
    """Create the test response.

    Args: 
        None

    Returns: 
        The created response (str)
    """
    response_body = '<html><body><h1>This is a simple response body for '\
        'test \"{}\"!</h1></body></html>\n'.format(__file__)

    response_status_line = 'HTTP/1.1 200 OK'
    response_headers = [
        response_status_line,
        'Content-Type: text/html; encoding=utf8',
        'Content-Length: ' + str(len(response_body)),
        'Connection: close',
        '\r\n', # Newline to end headers
    ]

    response = '\r\n'.join(response_headers) + response_body
    response = response.encode()

    return response


def send_test_response(client_sock, response):
    """Create the test response.

    Args: 
        client_sock (socket): the socket to send the request on
        response (str): the response to send

    Returns: 
        None
    """
    # Send the response one byte at a time, sleeping a little bit in-between
    # every byte
    for i in range(len(response)):
        client_sock.sendall(response[i:i+1])
        time.sleep(0.01)


def get_listen_sock(port):
    """Create a TCP socket, bind it to the requested port, and listen.

    Args: 
        port (int): The port to bind to

    Returns: 
        The created socket (socket).

    Raises:
        Socket errors
    """
    # create_server is a nice convenience function that calls socket(), bind(),
    # and listen() for the programmer.  However, since it is only available in
    # Python version 3.8, we won't use it.
    #address = ('', port)
    #s = socket.create_server(address, reuse_port=True, dualstack_ipv6=True)

    address = ('', port) 
    # Note: Using AF_INET and not AF_INET6 makes this not IPv4/IPv6 compliant
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    s.bind(address)
    s.listen(100)

    return s
    

def main():
    """A simple HTTP server that is *not* strictly compliant to the HTTP
    protocol.  In particular, this server entirely ignores the incoming message
    and returns a static response.  This server is primiarly useful for
    experimenting with whether or not a static response is HTTP compliant.

    Args: None

    Returns: None
    """
    # Use argparse to allow for easily changing the port
    parser = argparse.ArgumentParser(description='Simple server to test '
        'edge-cases in the HTTP protocol.')
    parser.add_argument('--port', required=True, type=int,
        help='The port to listen on.')
    args = parser.parse_args()
    port = args.port

    # Create the listening socket
    server_sock = get_listen_sock(port)

    while True:
        # Accept the connection
        client_sock, client_addr = server_sock.accept()

        # Ignore any request (not protocol compliant)

        # Get the test response
        response = get_test_response()

        # Print sending response for optional debugging
        #print('Sending response:')
        #print(response)
        
        # Send the rest response
        send_test_response(client_sock, response)

        # Close the connection for garbage collection
        client_sock.close()


if __name__ == "__main__":
    main()
