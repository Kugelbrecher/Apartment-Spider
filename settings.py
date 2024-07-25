import os
import logging

# apartment official websites
# nema chicago
NEMA_URL = 'https://www.rentnemachicago.com/availability#all'
# 1000m
M1000_URL = 'https://1000mchicago.com/floor-plans/?availability-tabs=apartments-tab'
# linea
LINEA_URL = 'https://lineachicago.com/floor-plans/?availability-tabs=apartments-tab'
# 1130
ELEVEN30_URL = 'https://1130smichigan.com/available-residences/'
# 1140
ELEVEN40_URL = 'https://www.live1140.com/availableunits'
# reed
REED_URL = 'https://thereedapts.com/floor-plans'
# elle
ELLE_URL = 'https://www.theellechicago.com/floorplans'
# grand central
GRAND_CENTRAL_URL = 'https://www.thegrandcentralapartments.com/floorplans'
# randolph tower
RANDOLPH_TOWER_URL = 'https://randolphtowercityapartments.com/apartment-floorplans/'

# arrive michigan
ARRIVE_MICHIGAN_URL = 'https://arrivemichiganavenue.com/floorplans/'


# postgresql database
DB_NAME = 'apartment_history'
DB_USER = 'niksun'
DB_PASSWORD = ''
DB_HOST = 'localhost'
DB_PORT = '5432'


# logging settings
LOG_LEVEL = logging.DEBUG    # default log level
LOG_FMT = '%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s: %(message)s'   # default log format
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # default date format
LOG_FILENAME = os.path.join(os.path.dirname(__file__), "logs", "log.log") # default log file name
