import sys
import traceback
from typing import Optional, cast

class ResearchAnalystException(Exception):
    def __init__(self, error_message, error_details: Optional[object] = None):
        # Normalize message to a string
        if isinstance(error_message, BaseException): # If the user passed an exception object, convert it into readable text (via str()).
            norm_msg = str(error_message)
        else:
            norm_msg = error_message
        
        # Resolve exc_info (supports: sys module, Exception object, or current context)
        exc_type = exc_value = exc_tb = None
        if error_details is None:
            exc_type, exc_value, exc_tb = sys.exc_info()
        else:
            if hasattr(error_details, "exc_info"): # e.g., sys
                exc_info_obj = cast(sys, error_details)
                exc_type, exc_value, exc_tb = exc_info_obj.exc_info()
            """
            If a real exception object is passed, extract:

             -   Its type (type(error_details))

             -   The exception instance

             -   Its traceback (__traceback__)
            """
            elif isinstance(error_details, Exception): # e.g., a raised exception
                exc_type, exc_value, exc_tb = type(error_details), error_details, error_details.__traceback__
            else:
                exc_type, exc_value, exc_tb = sys.exc_info()

        # walk up the stack to find the first non-ResearchAnalystException frame
        last_tb = exc_tb
        while last_tb and last_tb.tb_next:
            last_tb = last_tb.tb_next

        self.file_name = last_tb.tb_frame.f_code.co_filename if last_tb else "<unknown file>"
        self.lineno = last_tb.tb_lineno if last_tb else -1
        self.error_message = norm_msg

        # Full traceback as string if available
        if exc_type and exc_tb:
            self.traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb)) # Converts traceback into a multiline string using format_exception.
        else:
            self.traceback_str = "<no traceback available>"
        
        super().__init__(self.__str__()) # Calls the base Exception constructor.

        # This ensures that printing the exception prints a nice readable message.

    def __str__(self):
        # compact, logger-friendly message (no leading spaces)
        base = f"Error in [{self.file_name}] at line [{self.lineno}] | Message: {self.error_message}"
        if self.traceback_str:
            return f"{base}\nTraceback:\n{self.traceback_str}"
        return base

    def __repr__(self):
        return f"ResearchAnalysisException(file={self.filename!r}, line={self.lineno}, message={self.error_message!r})"

