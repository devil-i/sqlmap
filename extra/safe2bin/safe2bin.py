#!/usr/bin/env python2

"""
safe2bin.py - Simple safe(hex) to binary format converter

Copyright (c) 2006-2019 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from __future__ import print_function

import binascii
import re
import string
import os
import sys

from optparse import OptionError
from optparse import OptionParser

if sys.version_info >= (3, 0):
    xrange = range
    text_type = str
    string_types = (str,)
    unichr = chr
else:
    text_type = unicode
    string_types = (basestring,)

# Regex used for recognition of hex encoded characters
HEX_ENCODED_CHAR_REGEX = r"(?P<result>\\x[0-9A-Fa-f]{2})"

# Raw chars that will be safe encoded to their slash (\) representations (e.g. newline to \n)
SAFE_ENCODE_SLASH_REPLACEMENTS = "\t\n\r\x0b\x0c"

# Characters that don't need to be safe encoded
SAFE_CHARS = "".join([_ for _ in string.printable.replace('\\', '') if _ not in SAFE_ENCODE_SLASH_REPLACEMENTS])

# Prefix used for hex encoded values
HEX_ENCODED_PREFIX = r"\x"

# Strings used for temporary marking of hex encoded prefixes (to prevent double encoding)
HEX_ENCODED_PREFIX_MARKER = "__HEX_ENCODED_PREFIX__"

# String used for temporary marking of slash characters
SLASH_MARKER = "__SLASH__"

def safecharencode(value):
    """
    Returns safe representation of a given basestring value

    >>> safecharencode(u'test123')
    u'test123'
    >>> safecharencode(u'test\x01\x02\xff')
    u'test\\01\\02\\03\\ff'
    """

    retVal = value

    if isinstance(value, string_types):
        if any(_ not in SAFE_CHARS for _ in value):
            retVal = retVal.replace(HEX_ENCODED_PREFIX, HEX_ENCODED_PREFIX_MARKER)
            retVal = retVal.replace('\\', SLASH_MARKER)

            for char in SAFE_ENCODE_SLASH_REPLACEMENTS:
                retVal = retVal.replace(char, repr(char).strip('\''))

            for char in set(retVal):
                if not (char in string.printable or isinstance(value, text_type) and ord(char) >= 160):
                    retVal = retVal.replace(char, '\\x%02x' % ord(char))

            retVal = retVal.replace(SLASH_MARKER, "\\\\")
            retVal = retVal.replace(HEX_ENCODED_PREFIX_MARKER, HEX_ENCODED_PREFIX)
    elif isinstance(value, list):
        for i in xrange(len(value)):
            retVal[i] = safecharencode(value[i])

    return retVal

def safechardecode(value, binary=False):
    """
    Reverse function to safecharencode
    """

    retVal = value
    if isinstance(value, string_types):
        retVal = retVal.replace('\\\\', SLASH_MARKER)

        while True:
            match = re.search(HEX_ENCODED_CHAR_REGEX, retVal)
            if match:
                retVal = retVal.replace(match.group("result"), unichr(ord(binascii.unhexlify(match.group("result").lstrip("\\x")))))
            else:
                break

        for char in SAFE_ENCODE_SLASH_REPLACEMENTS[::-1]:
            retVal = retVal.replace(repr(char).strip('\''), char)

        retVal = retVal.replace(SLASH_MARKER, '\\')

        if binary:
            if isinstance(retVal, text_type):
                retVal = retVal.encode("utf8")

    elif isinstance(value, (list, tuple)):
        for i in xrange(len(value)):
            retVal[i] = safechardecode(value[i])

    return retVal

def main():
    usage = '%s -i <input file> [-o <output file>]' % sys.argv[0]
    parser = OptionParser(usage=usage, version='0.1')

    try:
        parser.add_option('-i', dest='inputFile', help='Input file')
        parser.add_option('-o', dest='outputFile', help='Output file')

        (args, _) = parser.parse_args()

        if not args.inputFile:
            parser.error('Missing the input file, -h for help')

    except (OptionError, TypeError) as ex:
        parser.error(ex)

    if not os.path.isfile(args.inputFile):
        print('ERROR: the provided input file \'%s\' is not a regular file' % args.inputFile)
        sys.exit(1)

    f = open(args.inputFile, 'r')
    data = f.read()
    f.close()

    if not args.outputFile:
        args.outputFile = args.inputFile + '.bin'

    f = open(args.outputFile, 'wb')
    f.write(safechardecode(data))
    f.close()

if __name__ == '__main__':
    main()
