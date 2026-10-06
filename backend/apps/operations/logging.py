import logging
import re


class SensitivePathFilter(logging.Filter):
    def filter(self, record):
        record.msg = re.sub(
            r"/(confirm|unsubscribe)/(?:one-click/)?[^/\s]+/",
            r"/\1/[redacted]/",
            record.getMessage(),
        )
        record.args = ()
        return True
