#!/usr/bin/env python
# Simple Python 2 test

print "Hello Python 2!"

import urllib2
import ConfigParser

def get_input():
    name = raw_input("Name: ")
    return name

def process():
    data = {"a": 1, "b": 2}
    for key in data.iterkeys():
        print "Key:", key

def divide_numbers():
    result = 10 / 3  # Integer division in Python 2
    print "Result:", result

if __name__ == "__main__":
    process()
    divide_numbers()
