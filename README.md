---
title: Homework 3 Part 2
description: A Barebones HTTP/1.1 Client
due: {{ site.hw3p2due }}
assigned: Saturday, February 1
additional_css: [syntax.css]
---

## {{ page.title }}: {{ page.description }}

##### **This assignment is not optional and is due at 11:59 pm on
Monday, April 13th.**

##### **You can access the homework starter code [here][hw3p2classroom].**

##### **Make sure to read the homework before starting. We have incorporated updated autograder submission and testing instructions.**

In this programming exercise, you will create a barebones web client.
While python includes a basic http client module `http.client`, this
assignment will serve as a learning experience for translating a
protocol into an implementation. One of your deliverables will be a
client that behaves identically to the command line program `curl` given
the `-f` flag (`curl -f`).  To do this, you will follow the HTTP/1.1
specification to build a program that can generate a request with the
`GET` method and process the subsequent HTTP reply.  Additionally, this
client must also support SSL and verify the certificate of pages that
you connect to.

There are three goals of this assignment:
1. Introduce you to using POSIX sockets for network communication in
an application.
2. Provide experience with correctly implementing a network protocol
given a specification.
3. Exercise your ability to understand test edge-cases in network
protocols.

The submission requirements and the grading for this assignment are
created with these goals in mind.  In short, each of these three goals
shapes this assignment as follows:
1. Edge-cases related to POSIX sockets will be tested for.  This
means that the auto-grader will be testing for both IPv4/IPv6 DNS
support and for correct behavior given partial data with the `send` and
`recv` system calls.
2. You are required to build a client that is *strictly* compliant with
the HTTP protocol specification (See [the RFC][http]).  As such,
edge-cases related to atypical messages will be tested, including
spacing, capitalization, and line-wrapping.  In general, the HTTP
standard is permissive. There are many different valid ways to
format requests, and your client is expected to accept any valid
response.
3. To demonstrate your understanding of the HTTP protocol specification,
you are required to create new test cases and include both the test
cases and a description of what aspect of compliance to the protocol the
test case covers.  

The rest of this assignment description is organized into the following
sections:
1. [Client Functionality](#client)
2. [HTTP/1.1 Overview](#http-overview)
3. [Skeleton Code](#skeleton)
4. [Test Cases](#testing)
5. [Grading](#grading)

## <a name="client"></a> Client functionality

As seen in class, HTTP is a stateless request-response protocol that consists
of an initial line, zero or more headers, and zero or more bytes of content.
Your program will implement a function, `retrieve_url`, which takes a url (as
a `str`) as its only argument, and uses the HTTP protocol to retrieve and
return the body's bytes (do not decode those bytes into a string). Consult
the book or your class notes for the basics of the HTTP protocol.

You may assume that the URL will not include a fragment, query string, or
authentication credentials. You are not required to follow any redirects -
only return bytes when receiving a `200` response from the server. If for
any reason your program cannot retrieve the resource correctly or the
server returns a response that is not a valid HTTP response,
`retrieve_url` should return `None`.

As a rule of thumb, you should assume that you are building a client
that behaves the same as `curl` when given the `-f` flag
{% raw %} (`curl -f <url>`).  {% endraw %} However, in any cases where
`curl` and this specification differ, your client should behave as
described in this document.  For example, in our testing, `curl` returns
a body when fetching the URL
[https://www.fieggen.com/shoelace](https://www.fieggen.com/shoelace),
even though the server returned a "301" Status-Code.  In this case, your
client should return `None` regardless of the behavior of `curl`,
because this is the behavior described in this assignment specification.

In addition to this basic HTTP/1.1 client functionality, you are
required to support HTTPS (SSL), and you are required to support
connecting to hosts that only have IPv6 addresses in addition to also
supporting IPv4 addresses.

### Validating HTTPS
Within the `retrieve_url` you will also be required to ensure that when
connecting to a HTTPS based website, your client ensures a valid
certificate is provided by the server. The `ssl` library in Python will
do this for you by default.  If the returned certificate is invalid
(expired, wrong host etc) and cannot be validated `retrieve_url` returns
`None`. To test your code in addition to the provided tests, there are
examples available at [badssl.com](https://badssl.com/).

### DNS support for IPv4 and IPv6 Addresses
In order for your client to connect to the servers specified by hostname
in the URL, your client must perform a DNS lookup.  Recall from class
that DNS can be used to map hostnames to either IPv4 or IPv6 addresses.
As such, your client is required to support finding and connecting to
both IPv4 and IPv6 addresses.

In python, this is done through the `getaddrinfo` function of the
`socket` module.  Importantly, this function returns both IPv4 and IPv6
addresses found from the DNS lookup.  Your client should then correctly
interpret the addresses it finds and try to connect to each one of these
addresses until at least one connection succeeds.  In other words, if
your client is unable to connect to an IPv4 address but is able to
connect to an IPv6 address, then this is not an error and your client
should continue to issue a request and read the response.  The same is
true if your client is not able to connect to an IPv6 address, but can
connect to an IPv4 address.


## <a name="http-overview"></a> HTTP/1.1 Overview

[The HTTP/1.1 RFC][http] specifies the HTTP/1.1 protocol.  Because you
are expected to build a client that is *strictly* compliant with the
HTTP/1.1 protocol, reading and understanding this RFC is important.  The
HTTP/1.1 protocol is very permissive.  For this homework, your
submission will be graded against simple custom HTTP servers that
generate unusual but protocol compliant responses, and your program is
expected to correctly process and accept these responses. Additionally,
to demonstrate your understanding of the HTTP protocol and the
correctness of your program, you are also required to create new HTTP
responses that are both valid and invalid and test for edge cases in the
HTTP protocol.

However, your HTTP client is not required to generate every type of HTTP
request nor handle every type of HTTP response.  Instead, you are only
required to generate requests with the "GET" method, and you are only
required to handle responses returned with the 200 status ("OK").

To help you correctly implement the HTTP protocol, the rest of this
section includes notes and tips on the aspects of the HTTP protocol that
you are required to implement.  However, you may also find it useful to
read James Marshall's excellent [HTTP Made Really
Easy](https://www.jmarshall.com/easy/http/#http1.1clients) under the
HTTP/1.1 clients subsection.

Note that the RFCs are your friends: if you're having trouble with
`Transfer-encoding`, check [the RFC][http] for hints!

### Text in HTTP

HTTP is a text-based protocol.  Correctly handling the different ways
that text can be formatted in the HTTP protocol is an important part of
building a client that correctly implements the HTTP protocol, and there
are a few subtleties of the HTTP protocol that are easy to get wrong:
* **CRLF**: From Section 2.2 of the RFC,
    "HTTP/1.1 defines the sequence CR LF as the end-of-line marker for
    all protocol elements except the entity-body (see appendix 19.3 for
    tolerant applications). The end-of-line marker within an entity-body
    is defined by its associated media type, as described in section
    3.7."

       CRLF           = CR LF

* **Case-Insensitive**: From Section 2.1 of the RFC, "Unless stated otherwise,
      the text is case-insensitive."
* **Implied \*LWS**: From Section 2.1 of the RFC,
    "The grammar described by this specification is word-based. Except
    where noted otherwise, linear white space (LWS) can be included
    between any two adjacent words (token or quoted-string), and between
    adjacent words and separators, without changing the interpretation
    of a field. At least one delimiter (LWS and/or separators) MUST
    exist between any two tokens (for the definition of "token" below),
    since they would otherwise be interpreted as a single token." ->
    This means that extra whitespace in headers is still a valid HTTP
    header.
* **Special characters and quoted strings**: From Section 2.2 of the
    RFC, "Many HTTP/1.1 header field values consist of words separated
    by LWS or special characters. These special characters MUST be in a
    quoted string to be used within a parameter value (as defined in
    section 3.6)."<br>

       separators     = "(" | ")" | "<" | ">" | "@"
                      | "," | ";" | ":" | "\" | <">
                      | "/" | "[" | "]" | "?" | "="
                      | "{" | "}" | SP | HT

    and "A string of text is parsed as a single word if it is quoted
    using double-quote marks."

       quoted-string  = ( <"> *(qdtext | quoted-pair ) <"> )
       qdtext         = <any TEXT except <">>
* **Comments**: From Section 2.2 of the RFC,
    "Comments can be included in some HTTP header fields by surrounding
    the comment text with parentheses. Comments are only allowed in
    fields containing "comment" as part of their field value definition.
    In all other fields, parentheses are considered part of the field
    value."

### HTTP GET Requests

GET is the only "Method" of HTTP request that your client is required to
support.  For reference, HTTP requests are specified in Section 5 of
[the RFC][http].  From this section, we can see that a request is
defined as follows:

    Request   = Request-Line              ; Section 5.1
                *(( general-header        ; Section 4.5
                 | request-header         ; Section 5.3
                 | entity-header ) CRLF)  ; Section 7.1
                CRLF
                [ message-body ]          ; Section 4.3

To generate a policy-compliant GET request, you will have to generate a
Request-Line, a `Host:` header, and a `Connection: close` header, and
merge them together with the appropriate CRLF newlines (`\r\n`).

In more detail:
* **Request-Line**: From Section 5.1 of the RFC:
    "The Request-Line begins with a method token, followed by the
    Request-URI and the protocol version, and ending with CRLF. The
    elements are separated by SP characters. No CR or LF is allowed
    except in the final CRLF sequence."

        Request-Line   = Method SP Request-URI SP HTTP-Version CRLF

    * **GET Method**: Because you are only supporting "GET", the method
      in your request-line should always be "GET" (Section 5.1.1).
    * **absoluteURI**: From Section 5.1.2,
        "The absoluteURI form is REQUIRED when the request is being made
        to a proxy. The proxy is requested to forward the request or
        service it from a valid cache, and return the response. Note
        that the proxy MAY forward the request on to another proxy or
        directly to the server specified by the absoluteURI. In order to
        avoid request loops, a proxy MUST be able to recognize all of
        its server names, including any aliases, local variations, and
        the numeric IP address. An example Request-Line would be:"

           GET http://www.w3.org/pub/WWW/TheProject.html HTTP/1.1

* **Host Header**: From Section 14.23, "A client MUST include a Host
    header field in all HTTP/1.1 request messages.", and "The Host
    request-header field specifies the Internet host and port number of
    the resource being requested, as obtained from the original URI
    given by the user or referring resource (generally an HTTP URL, as
    described in section 3.2.2). The Host field value MUST represent the
    naming authority of the origin server or gateway given by the
    original URL. This allows the origin server or gateway to
    differentiate between internally-ambiguous URLs, such as the root
    "/" URL of a server for multiple host names on a single IP address."

       Host = "Host" ":" host [ ":" port ] ; Section 3.2.2

   * See sections 5.2 and 19.6.1.1 for other requirements relating
     to Host.

* **Connection: close**:  For simplicity, your client is not required to
    support persistent connections.  However, From Section 19.6.2,
    "Persistent connections are the default for HTTP/1.1 messages; we
    introduce a new keyword (Connection: close) for declaring
    non-persistence. See section 14.10."
    * From Section 14.10,
      "HTTP/1.1 defines the "close" connection option for the sender to
      signal that the connection will be closed after completion of the
      response. For example,

            Connection: close

      in either the request or the response header fields indicates
      that the connection SHOULD NOT be considered `persistent' (section
      8.1) after the current request/response is complete.

      HTTP/1.1 applications that do not support persistent connections MUST
      include the "close" connection option in every message."


### HTTP Responses

Your client only needs to support responses that come with a status-code
of "200" (OK).  To do this, your client will need to be able to
correctly parse and validate HTTP responses (Section 6).  From [the
RFC][http], "After receiving and interpreting a request message, a
server responds with an HTTP response message."

       Response      = Status-Line               ; Section 6.1
                       *(( general-header        ; Section 4.5
                        | response-header        ; Section 6.2
                        | entity-header ) CRLF)  ; Section 7.1
                       CRLF
                       [ message-body ]          ; Section 7.2

Most of the difficulty in building a client that is *strictly* compliant
with the HTTP protocol is in correctly parsing and validating HTTP
Responses.  This is because, unlike requests, whose format is completely
controlled by your code, responses are received over the network from a
server that your client connects to, and different servers are allowed
to format their responses differently by the HTTP protocol standard.

Their are two primary components to an HTTP response: headers and the
message-body.  The rest of this section describes these components in
more detail.

#### HTTP Response Headers

HTTP response headers start with a Status-Line, are optionally followed
by some number of headers, and are terminated with a CRLF (`\r\n`).
In more detail:

* **Status-Line**: From Section 6.1, 
    "The first line of a Response message is the Status-Line, consisting
    of the protocol version followed by a numeric status code and its
    associated textual phrase, with each element separated by SP
    characters. No CR or LF is allowed except in the final CRLF
    sequence."

       Status-Line = HTTP-Version SP Status-Code SP Reason-Phrase CRLF

    * **Status-Code**: Section 6.1.1 defines the different status codes
        in HTTP.  Your client must ignore all responses (return `None`)
        that do not have the "200" (OK) Status code.
    * **Reason-Phrase**: From Section 6.1.1, "The Reason-Phrase is
        intended to give a short textual description of the Status-Code.
        The Status-Code is intended for use by automata and the
        Reason-Phrase is intended for the human user. **The client is
        not required to examine or display the Reason- Phrase.**".
        Also, "The reason phrases listed here are only recommendations
        -- they MAY be replaced by local equivalents without affecting
        the protocol."

              Reason-Phrase  = *<TEXT, excluding CR, LF>

* **Content-Length Header**: From Section 14.13 of the RFC:
   "The Content-Length entity-header field indicates the size of the
   entity-body, in decimal number of OCTETs, sent to the recipient or,
   in the case of the HEAD method, the size of the entity-body that
   would have been sent had the request been a GET.

       Content-Length    = "Content-Length" ":" 1*DIGIT

   An example is

       Content-Length: 3495

   Applications SHOULD use this field to indicate the transfer-length of
   the message-body, unless this is prohibited by the rules in section
   4.4.

   Any Content-Length greater than or equal to zero is a valid value.
   Section 4.4 describes how to determine the length of a message-body
   if a Content-Length is not given."

* **Transfer-Encoding: chunked**:  From Section 4.4 of the RFC:
    "All HTTP/1.1 applications that receive entities MUST accept the
    "chunked" transfer-coding (section 3.6), thus allowing this
    mechanism to be used for messages when the message length cannot be
    determined in advance."  Thus, although your client is not required
    to support all different types of transfer-coding, it *must*
    support the "chunked" transfer-coding.

    From Section 14.41, "14.41 Transfer-Encoding

    The Transfer-Encoding general-header field indicates what (if any)
    type of transformation has been applied to the message body in order
    to safely transfer it between the sender and the recipient. This
    differs from the content-coding in that the transfer-coding is a
    property of the message, not of the entity.

      Transfer-Encoding       = "Transfer-Encoding" ":" 1#transfer-coding

    Transfer-codings are defined in section 3.6. An example is:"

      Transfer-Encoding: chunked

    Also, from SEction 14.39, " If the TE field-value is empty or if no
    TE field is present, the only transfer-coding  is "chunked". A
    message with no transfer-coding is always acceptable."

* **Message Length**: Your client should correctly handle servers that
  use a variety of different ways to indicate message length.  This
  includes `Transfer-Encoding: chunked`, the `Content-Length:` header
  field, and even by the server closing the connection.
  
  To provide some more details on how message length is determined in
  HTTP/1.1, from Section 4.4 of the RFC:

    "2.If a Transfer-Encoding header field (section 14.41) is present and
     has any value other than "identity", then the transfer-length is
     defined by use of the "chunked" transfer-coding (section 3.6),
     unless the message is terminated by closing the connection.

    3.If a Content-Length header field (section 14.13) is present, its
    decimal value in OCTETs represents both the entity-length and the
    transfer-length. The Content-Length header field MUST NOT be sent if
    these two lengths are different (i.e., if a Transfer-Encoding header
    field is present). If a message is received with both a
    Transfer-Encoding header field and a Content-Length header field,
    the latter MUST be ignored.

    5.By the server closing the connection. (Closing the connection
    cannot be used to indicate the end of a request body, since that
    would leave no possibility for the server to send back a response.)"

* **Header field continuation/LWS**:  From Section 2.2 of the RFC, "A CRLF
  is allowed in the definition of
  TEXT only as part of a header field continuation."  Also from Section
  2.2: "HTTP/1.1 header field values can be folded onto multiple
    lines if the continuation line begins with a space or horizontal
    tab. All linear white space, including folding, has the same
    semantics as SP. A recipient MAY replace any linear white space with
    a single SP before interpreting the field value or forwarding the
    message downstream."  **Note: you should expect your program to be
    tested against responses with header field continuations.**

       LWS            = [CRLF] 1*( SP | HT )

#### HTTP Response Bodies

All messages with a "200" Status-Code must include a message-body,
although it *may* be of zero length (Section 4.3).

From Section 4.3 of the RFC, "The message-body (if any) of an HTTP
message is used to carry the entity-body associated with the request or
response. The message-body differs from the entity-body only when a
transfer-coding has been applied, as indicated by the Transfer-Encoding
header field (section 14.41).

       message-body = entity-body
                    | <entity-body encoded as per Transfer-Encoding>

Transfer-Encoding MUST be used to indicate any transfer-codings
applied by an application to ensure safe and proper transfer of the
message. Transfer-Encoding is a property of the message, not of the
entity, and thus MAY be added or removed by any application along the
request/response chain. (However, section 3.6 places restrictions on
when certain transfer-codings may be used.)"

Your client should support the "chunked" Transfer-Encoding.
Additionally, your client should support a server using "Content-Length"
and closing a connection to determine the end of a message body.

A few more details:
* **Content-Length**: From Section 10.2.7 of the RFC,
    "If a Content-Length header field is present in the response, its
    value MUST match the actual number of OCTETs transmitted in the
    message-body."

    This implies that reading a response body given a content length is
    easy.  You should *repeatedly* use the `recv` system call to read
    data from the socket until the correct number of OCTETs (bytes) have
    been read.

* **Transfer-Encoding: chunked**:  From Section 3.6.1 of the RFC:
   "The chunked encoding modifies the body of a message in order to
   transfer it as a series of chunks, each with its own size indicator,
   followed by an OPTIONAL trailer containing entity-header fields. This
   allows dynamically produced content to be transferred along with the
   information necessary for the recipient to verify that it has
   received the full message.

       Chunked-Body   = *chunk
                        last-chunk
                        trailer
                        CRLF

       chunk          = chunk-size [ chunk-extension ] CRLF
                        chunk-data CRLF
       chunk-size     = 1*HEX
       last-chunk     = 1*("0") [ chunk-extension ] CRLF

       chunk-extension= *( ";" chunk-ext-name [ "=" chunk-ext-val ] )
       chunk-ext-name = token
       chunk-ext-val  = token | quoted-string
       chunk-data     = chunk-size(OCTET)
       trailer        = *(entity-header CRLF)

   The chunk-size field is a string of hex digits indicating the size of
   the chunk. The chunked encoding is ended by any chunk whose size is
   zero, followed by the trailer, which is terminated by an empty line.

   The trailer allows the sender to include additional HTTP header
   fields at the end of the message. The Trailer header field can be
   used to indicate which header fields are included in a trailer (see
   section 14.40)."

    * **Algorithm for decoding the chunked transfer-coding**:
        From Section 19.4.6 of the RFC,
        "A process for decoding the "chunked" transfer-coding (section 3.6)

           length := 0
           read chunk-size, chunk-extension (if any) and CRLF
           while (chunk-size > 0) {
              read chunk-data and CRLF
              append chunk-data to entity-body
              length := length + chunk-size
              read chunk-size and CRLF
           }
           read entity-header
           while (entity-header not empty) {
              append entity-header to existing header fields
              read entity-header
           }
           Content-Length := length
           Remove "chunked" from Transfer-Encoding

    * **; chunk-extension**: Note that every line containing a chunk-size may
        also *optionally* have a `;` character followed by a
        chunk-extension.


## <a name="skeleton"></a> Skeleton Code
A well-documented and commented template is provided in this repository,
as `hw3.py`. This contains the necessary modules you need to complete
this homework.   You are likely **not allowed** to import any additional
modules.  Specifically, unless you are otherwise granted permission via
Piazza, you are not allowed to import any additional modules. 

The provided skeleton code contains many mostly empty functions.  You
**are not required** to use all of these functions.  In other words, you
are allowed to create your own new functions and modify the control flow
of the application.  That said, you also do not have to create any new
functions to implement a correct client.  The provided functions,
implemented correctly, are sufficient.

However, if you change the control flow of the provided skeleton
application, you are required to explain why in your WRITEUP.  Further,
as always, you are required to document any outside sources that you
consulted.

The rest of this section describes the different functions in the
skeleton code in more detail:

* `parse_url`: This function should take in the URL and return a
  (scheme, hostname, port, path) tuple.  To implement this function, you
  are encouraged to use the `urlparse` function that is already imported
  for you.  However, you will still have to perform error checking to
  validate the URL and to pick the default ports for HTTP and HTTPS URLs
  if a port is not specified.

* `open_connection`: This function takes as input a hostname and port
  and returns an open socket.  To implement this function so that it
  correctly handles DNS lookups for both IPv4 and IPv6 addresses, you
  will need to use the `socket.getaddrinfo()`, `socket.socket()`, and
  `s.connect()` functions.

* `wrap_socket_ssl`: This function takes as input a socket, validates
  the server's certificates and hostname, and returns a wrapped socket.
  All of the SSL functionality of your client can be contained in this
  one function.

* `gen_http_req`: This function takes as input a hostname, port, and
  path and returns an encoded (correct) HTTP GET Request with the
  appropriate headers.  Note that you will likely need to call the
  `str.encode()` function of a string to go from a Python string to
  bytes.  You may also want to pass the input URL to this function as
  well.

* `send_req`: Sends an HTTP GET request (bytes) on a socket.  Returns
  True on success and False on error.  To implement this function, you
  are welcome to use either the `s.send()` or `s.sendall()` functions.
  However, if you use `s.send()`, you must ensure that the *entire*
  request is sent, even given that send can return after only sending a
  partial message.  Further, both of these functions can raise
  exceptions, which should be caught.

* `parse_headers`: Given the raw header bytes received from the socket,
  parse the headers.  This includes separating the Status-Line, and this
  includes getting a list of field name, field value pairs.  Note that
  correctly implementing this function requires support for variable
  amounts of white space, variable cases (case-insensitivity), and
  folded field values.  If the headers are not correctly formatted so
  that they can be parsed, this is an error and `None` should be
  returned for the body.

* `check_status_line`: Check if the status line is correct.  This means
  that any valid status line should be accepted.  Important things to
  check for in this function include case-insensitivity, support for
  white space, a status value of "200", and tolerating the absence of
  the optional Reason-Phrase.

* `validate_headers`: Validate all of the headers, including the
  Status-Line.  Once again, this function is required to *strictly*
  enforce the HTTP protocol while also ensuring that it accepts *all*
  headers that are protocol-compliant.  

* `get_body_len_info`: Check the headers to determine how long the body
  will be.  Note that if no "Content-Length" is specified, and the
  "Transfer-Encoding" field is not chunked, this is still not
  necessarily an error.

* `get_body_content_len`: Get the body given a Content-Length header was
  found.  Takes as arguments a socket s, any bytes of the body that have
  already been ready as `body_start`, and the length of the body from
  the Content-Length field value.  This function should use `recv` to
  get the response.  Note that `recv` is allowed to return less than the
  requested amount of bytes (including 0).  As a result, you should call
  `recv` until you have received all of the bytes specified by the
  protocol.

* `get_body_chunked`: Get the body given `Transfer-Encoding: chunked`.
  Takes as arguments a socket s and any bytes of the body that have
  already been ready as `body_start`.  See Section 19.4.6 of [the
  RFC][http] for pseudo-code on how to decode chunked messages.

* `read_resp`: Read an HTTP response from a socket s given that a
  request has already been written to the socket.  Returns None if the
  response is not a valid HTTP response with a Status-Code of "200",
  otherwise returns the body of the response.

* `retrieve_url`: Given a URL, issue an HTTP GET Request to fetch the
  content at this URL.  If any errors are encountered, or the response
  is not a valid HTTP Response, then None is returned.  Otherwise, the
  body is returned as a bytestring (bytes).


## <a name="testing"></a> Test Cases

As part of [the grading](grading) for this assignment, you are required
to create new test cases that exercise your program and demonstrate your
understanding of the HTTP protocol and its corner cases.  To help you
with this step, we are providing you with 1) test cases that compare
your program against the output of `curl -f` and 2) simple example test
HTTP servers that you can use to test different response headers and
bodies against both your own program.  The test harness is located in
`tester.py`.  The example test servers are located in
`tests/test_server0*.py`.

Your task for this assignment is to then follow the example test cases
and create your own new tests.  This includes two types of tests: 1) new
URLs to test your program against, and 2) new simple static HTTP servers
that demonstrate your knowledge of edge-cases in the HTTP protocol and
ability to test your program against curl.  Also, instead of requiring a
set amount of student test cases, you are instead required to submit all
of the test cases that you create and then explain in the documentation
in each individual write-up what edge-cases these test against and why
you believe that all of the tests you have created are sufficient for
testing the correctness of your program.

### Running Tests and Example Test Cases

Running the test cases is simple, at least in the Ubuntu environment
that the scripts were developed it.  The entire test harness can be run
by typing 
- Note: If there are any Windows and MacOS errors, they should be
  discussed on [Piazza][piazza]

If everything is setup correctly, running `./tester.py --hw3-path
hw3.py` should correctly run your program for all of the test cases that
you configured in `./tester.py`, which includes custom static python
HTTP servers that you have created in the `./tests/` folder.  See the
individual files for more documentation, but, to give an overview, here
are some important notes:
- Add all of your custom HTTP servers to the list `TEST_SERVERS` in
  `tester.py`.  Note that this functionality assumes that the test
  servers are executable files on your system.  This is made possibly
  easily on Unix platforms with the shebang used in the examples, but
  this may not be as simple on Windows platforms.  Note that you can
  either modify it or skip it entirely and just **ensure by hand that
  your test servers are running before you run this test script if this
  is not working for you**.
- Add all of the URLs that you would like to compare against to the
  `TEST_CASES` list in `tester.py`.  Note that this should include any
  local URLs and ports (e.g., `127.0.0.1:4500`)
- In cases where this assignment specification and the output of the
  script differ, this assignment specification is correct.
    - Any case where you believe the output of this script is incorrect,
      for any reason, is an interesting test case.  Note that all test
      cases that are sufficiently interesting are worth extra credit.
      This inludes errors in our test infrastructure, and this also
      includes suspected errors in applications like curl and Firefox.

There is a collection of example test HTTP servers in the `./test/`
directory.  Here are a few important notes:
- The `tests/test_server.py` application is intended to be the basis for
  all of your example HTTP test servers.  You are encourage to copy and
  modify this file in any way you need.
- Part of your grading is upon the documentation for the test cases that
  you create, and the place to do so is inside the source file that you
  create for each test server.  The example servers in
  `tests/test_server0*.py` contain example test documentation that you
  should follow.


## <a name="grading"></a> Submission and Grading

For this homework we will be using an autograder to grade your work, and
`./tester.py` is exactly the autograder that we will use.  Like before,
you can create as many backups as you like using `git commit -a` and
`git push`. 

There is a total of **100 points** on this assignment, with extra bonus
points being awarded for exceptional new test cases.  Additionally,
there are extra credit points available for finding bugs in any part of
this assignment infrastructure.

The points for this assignment are broken down as follows:
* **50 Points**: Correctness of the student HTTP client
* **35 Points**: New test cases (including documentation)
* **15 Points**: Code style for both HTTP clients and test cases


## Submission
You will be making the submission for this homework through github.

The files which will be submitted through github:
* `hw3.py`: This file will contain your version of the `retrieve_url`


To submit your work, run `git commit -a` and `git push`. Like previously, you are allowed to make multiple submissions 
but you have limited attempts with the grader.

## Due Date and Logistics

* This assignment is due at the at 11:59 pm on Monday, April 13th.

* If you have any questions please use the [Piazza][piazza] discussion forum.

[http]: https://www.ietf.org/rfc/rfc2616.txt
[hw3p2classroom]: TODO
[piazza]: {{ site.discussion }}
