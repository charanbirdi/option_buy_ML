""" 
this is best link and super easy
https://realpython.com/python-logging/#using-handlers

I take formatting class from here
https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
https://www.toptal.com/python/in-depth-python-logging

"""


import logging

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
    
    



    
def logging_function():
    
    # Create a custom logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('option_strategies.log')
        
    # Create formatters and add it to handlers
    #c_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)")
    f_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)")
    
    c_handler.setFormatter(CustomFormatter())
    f_handler.setFormatter(f_format)
    
    
    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.DEBUG)
    #logger.setLevel(logging.DEBUG)
    
    # Add handlers to the logger
    #if not logger.handlers:
    if True:
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)
        
    logger.propagate = False
       
    
    return logger


if __name__ == '__main__':
    """
    How to clean log file
    It might be better to truncate the file instead of removing it. 
    The easiest solution is to reopen the file for writing from your clearing function and close it:
    """
    
    
    #with open('option_strategies.log', 'w') as file:
    #    print("opened")
        #file.save
    #    pass
    
    # logger = logging.getLogger()
    # while logger.hasHandlers():
    #     logger.removeHandler(logger.handlers[0])     
    
    
    logger = logging_function()
    #logger.propagate = False
    

    

    # The demo test code
    logger.debug("The debug")
    logger.info("The info")
    logger.warning("The warn")
    logger.error("The error")
    logger.critical("The critical")