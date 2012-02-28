#!/usr/bin/env python

__author__ = 'Brian K. Jones'
__email__ = 'bkjones@gmail.com'

import unittest2 as unittest
from mock import Mock, patch, patch_object
from cmd import Cmd
from StringIO import StringIO
from bunnyq import Bunny

class TestBunny(unittest.TestCase):
    def setUp(self):
        Bunny.request = Mock()
        Bunny.do_connect = Mock(return_value=True)
        self.b = Bunny('foo', 9090, 'guest', 'guest')

    def test_instance(self):
        host = 'foo.bar'
        port = 9090
        user = 'guest'
        password = 'guest'
        b = Bunny(host, port, user, password)
        self.assertIsInstance(b, Bunny)
        self.assertIsInstance(b, Cmd)

    def test_list_vhost(self):
        self.b.request.return_value = [{'name': 'v1', 'foo': 'bar'},
                                     {'name': 'v2', 'baz': 'quux'}]
        sout = StringIO()
        expected_out = "v1\nv2\n"
        with patch('sys.stdout', new=sout) as out:
            self.b.do_list_vhosts(None)
            self.assertEqual(expected_out, out.getvalue())







