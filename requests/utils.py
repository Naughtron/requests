# -*- coding: utf-8 -*-

"""
requests.utils
~~~~~~~~~~~~~~

This module provides utlity functions that are used within Requests
that are also useful for external consumption.

"""

import cgi
import cookielib
import re
import zlib


def dict_from_cookiejar(cj):
    """Returns a key/value dictionary from a CookieJar.

    :param cj: CookieJar object to extract cookies from.
    """

    cookie_dict = {}

    for _, cookies in cj._cookies.items():
        for _, cookies in cookies.items():
            for cookie in cookies.values():
                # print cookie
                cookie_dict[cookie.name] = cookie.value

    return cookie_dict


def cookiejar_from_dict(cookie_dict):
    """Returns a CookieJar from a key/value dictionary.

    :param cookie_dict: Dict of key/values to insert into CookieJar.
    """

    # return cookiejar if one was passed in
    if isinstance(cookie_dict, cookielib.CookieJar):
        return cookie_dict

    # create cookiejar
    cj = cookielib.CookieJar()

    cj = add_dict_to_cookiejar(cj, cookie_dict)

    return cj


def add_dict_to_cookiejar(cj, cookie_dict):
    """Returns a CookieJar from a key/value dictionary.

    :param cj: CookieJar to insert cookies into.
    :param cookie_dict: Dict of key/values to insert into CookieJar.
    """

    for k, v in cookie_dict.items():

        cookie = cookielib.Cookie(
            version=0,
            name=k,
            value=v,
            port=None,
            port_specified=False,
            domain='',
            domain_specified=False,
            domain_initial_dot=False,
            path='/',
            path_specified=True,
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={'HttpOnly': None},
            rfc2109=False
        )

        # add cookie to cookiejar
        cj.set_cookie(cookie)

    return cj


def get_encodings_from_content(content):
    """Returns encodings from given content string.

    :param content: bytestring to extract encodings from.
    """

    charset_re = re.compile(r'<meta.*?charset=["\']*(.+?)["\'>]', flags=re.I)

    return charset_re.findall(content)


def get_encoding_from_headers(headers):
    """Returns encodings from given HTTP Header Dict.

    :param headers: dictionary to extract encoding from.
    """

    content_type = headers.get('content-type')
    content_type, params = cgi.parse_header(content_type)

    if 'charset' in params:
        return params['charset'].strip("'\"")


def unicode_from_html(content):
    """Attempts to decode an HTML string into unicode.
    If unsuccessful, the original content is returned.
    """

    encodings = get_encodings_from_content(content)

    for encoding in encodings:

        try:
            return unicode(content, encoding)
        except (UnicodeError, TypeError):
            pass

        return content


def get_unicode_from_response(r):
    """Returns the requested content back in unicode.

    :param r: Reponse object to get unicode content from.

    Tried:

    1. charset from content-type

    2. every encodings from ``<meta ... charset=XXX>``

    3. fall back and replace all unicode characters

    """

    tried_encodings = []

    # Try charset from content-type
    encoding = get_encoding_from_headers(r.headers)

    if encoding:
        try:
            return unicode(r.content, encoding)
        except UnicodeError:
            tried_encodings.append(encoding)

    # Fall back:
    try:
        return unicode(r.content, encoding, errors='replace')
    except TypeError:
        return r.content


def decode_gzip(content):
    """Return gzip-decoded string.

    :param content: bytestring to gzip-decode.
    """

    return zlib.decompress(content, 16+zlib.MAX_WBITS)


def curl_from_request(request):
    """Creates a curl command from the request."""

    #TODO - Files
    #TODO - OAuth
    #TODO - Cookies

    #: -L/--location - if there is a redirect, redo request on the new place
    curl = 'curl -L '

    #: -u/--user - Specify the user name and password to use for server auth. 
    auth = ''
    if request.auth is not None:
       auth = '-u "%s:%s" ' % (request.auth.username, request.auth.password) 

    if request.method.upper() == 'HEAD':
        #: -I/--head - fetch headers only
        method = '-I '
    else:
        #: -X/--request - specify request method
        method = '-X %s ' % request.method.upper()

    #: -H/--header - Extra header to use when getting a web page
    header = ''
    if request.headers:
        header = header.join(['-H "%s:%s" ' % (k, v) for k, v in request.headers.iteritems()])

    data = ''
    if request.method in ('PUT', 'POST', 'PATCH'):
        #: -d/--data - send specified data in post request.
        if isinstance(request.data, (list, tuple)):
            data = data.join(['-d "%s=%s" ' % (k, v) for (k, v) in request.data])
        elif request._enc_data is not None:
            data = '-d %s ' % (request._enc_data)

    #: Params handled in _build_url
    return curl + auth + method + header + data + '"' + request._build_url() + '"'
