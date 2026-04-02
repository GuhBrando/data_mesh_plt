class Email:
    """
    Value object representing an email address.
    """

    def __init__(self, address: str):
        if not self._validate_email(address):
            raise ValueError(f"Invalid email address: {address}")
        self.address = address

    def _validate_email(self, address: str) -> bool:
        """Validates the email address format."""
        import re

        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(email_regex, address) is not None

    def __repr__(self):
        return self.address

    def __eq__(self, other):
        if isinstance(other, Email):
            return self.address == other.address
        return False
