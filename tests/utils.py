class MockParser:
    """
    Small class that contains the necessary functions in order to test custom
    validation functions used with the argparse module
    """

    def __init__(self):
        self.error_msg = None

    def error(self, value=None):
        self.error_msg = value

    def get_error(self):
        return self.error_msg
