import logging

def logMessage(msg:str, type:str):
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='comLog.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s')
    logger.info(type + " " + str(msg))
