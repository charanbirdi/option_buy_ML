import logging

def logging_function():
    

    stream = logging.StreamHandler()
    stream.setLevel(logging.INFO)
    streamformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
    stream.setFormatter(streamformat)


    optionlogs = logging.getLogger(__name__)
    optionlogs.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(stream)

    file = logging.FileHandler("option_logs.log")
    optionlogs.addHandler(file)    
    
    return optionlogs






if __name__ == '__main__':
    optionlogs = logging_function()

    # The demo test code
    optionlogs.debug("The debug")
    optionlogs.info("The info")
    optionlogs.warning("The warn")
    optionlogs.error("The error")
    optionlogs.critical("The critical")