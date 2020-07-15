#!/usr/bin/env python3

import argparse
import importlib.util
import os
import pathlib
import shlex
import subprocess
import sys
import time

# All paths must be either absolute or relative to the directory from which you
# are running this script.
TEST_SERVERS = [
    ('tests/test_server.py', 4500),
    ('tests/test_server01.py', 4501),
    ('tests/test_server02.py', 4502),
    ('tests/test_server03.py', 4503),
]

TEST_CASES = [
    'http://www.example.com',
    'http://127.0.0.1:4500',
    'http://127.0.0.1:4501',
    'http://127.0.0.1:4502',
    'http://127.0.0.1:4503',
]

# Pretty print test passing/failing output
PASS_FMT_STR = 'Case {} -> \033[1m URL: {}\u001b[32m \u25CF  Pass\033[0m'
FAIL_FMT_STR = 'Case {} -> \033[1m URL: {}\u001b[31m \u25CF  Failed\033[0m'

def start_test_servers():
    """A function to start the test servers.

    Args:
        None

    Returns:
        A list of the server processes that need to be terminated later.

    Notes:
        This function assumes that the test servers are executable files.  This
        is made possibly easily on Unix platforms with the shebang used in the
        examples, but this may not be as simple on Windows platforms.  If this
        is not working for you, you can either modify it or skip it entirely
        and just ensure by hand that your test servers are running before you
        run this test script.
    """
    servers = []
    for test_server_path, port in TEST_SERVERS:
        cmd = '{} --port {}'.format(test_server_path, port)
        args = shlex.split(cmd)
        server = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        servers.append(server)
    return servers

def get_url_curl(url):
    """A function to get a URL via curl.

    Args:
        None

    Returns:
        The body returned from curl.

    Notes:
        This function has not been tested on Windows.  I am interested in
        learning if it works on any Windows platforms.
    """
    cmd = 'curl -f {}'.format(url)
    args = shlex.split(cmd)
    process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    #XXX: Workaround for comparing errors in curl versus errors in the student
    # code because curl returns '' on error, while the student code is required
    # to return None.  Note that this workaround may not be correct in all
    # cases.  For example, this is incorrect if a test server returns an empty
    # body.  As such, it is best for test servers to not return an empty body,
    # or, if desired, then this function needs to be improved.
    if len(stdout) == 0:
        return None
    else:
        return stdout


def load_student_hw(hw3_path):
    """Load the provided student code as a callable module

    Args:
        hw3_path (str): The path to the student's code

    Returns:
        The loaded code as a callable module
    """
    try:
        spec = importlib.util.spec_from_file_location('hw3', str(hw3_path))
        student_hw = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(student_hw)
    except:
        print("Unable to load hw3.py")
        sys.exit(1)
    return student_hw


def main():
    """Test the student's code against curl for a list of test URLs.  This
    program will also optionally start test servers as well, if requested.

    Args:
        None (sys.argv is documented with the '--help' string)

    Returns:
        None
    """
    # Use argparse to allow for easily changing the port
    parser = argparse.ArgumentParser(description='Simple tester to start '
        'test servers and then compare against curl.')
    parser.add_argument('--hw3-path', required=True,
        help='The path to the hw3 to be tested.')
    args = parser.parse_args()
    hw3_path = args.hw3_path

    # Load the student code
    student_hw = load_student_hw(hw3_path)

    # Start the servers
    servers = start_test_servers()
    time.sleep(1)

    # Test the URLs
    for index, url in enumerate(TEST_CASES):
        try:
            student_body = student_hw.retrieve_url(url)
            curl_body = get_url_curl(url)
            if student_body == curl_body:
                print(PASS_FMT_STR.format(index, url))
            else:
                print(FAIL_FMT_STR.format(index, url))
        except:
            print(FAIL_FMT_STR.format(index, url))

    # Garbage collection: Kill all of the started servers
    for server in servers:
        server.terminate()


if __name__ == "__main__":
    main()
