import os
import sys
import unittest
sys.path.append("..")

import app

class BasicTests(unittest.TestCase):

    ############################
    #### setup and teardown ####
    ############################

    # executed prior to each test
    def setUp(self):
        pass

    # executed after each test
    def tearDown(self):
        pass

###############
#### tests ####
###############

    def test_main_page(self):
        # response = self.get('/', follow_redirects=True)
        # self.assertEqual(response.status_code, 200)
        pass
    

class HelperTests(unittest.TestCase):
    
    def test_sort_names(self):
        ### WRITE TEST CODE HERE
        self.assertEqual(app._sort_names(["Alexander Jones", "Sebastian Heath"]), ["Sebastian Heath", "Alexander Jones"])

        pass

    
if __name__ == "__main__":
    unittest.main()
