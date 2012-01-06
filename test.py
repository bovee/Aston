#!/usr/bin/python2.7

import unittest

class MainTest(unittest.TestCase):
    def testMethod(self):
        self.assertEqual(1+2,3,'1+2 == 3')

class PeakTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def testArea(self):
        self.assertEqual(2+3,4,'2+3 == 5')

    def testLength(self):
        self.assertEqual(8-4,5,'8-4 == 4')

unittest.main()
