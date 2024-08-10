# package import statement
from SmartApi import SmartConnect #or from SmartApi.smartConnect import SmartConnect
import pyotp

api_key = 'oPvM0VnS' #
clientId = 'C52284659'
pwd = '1030'
smartApi = SmartConnect(api_key)
token = "PGAFWLOTMLQKIR3EMWOGHU6KVY"
totp=pyotp.TOTP(token).now()


# login api call

data = smartApi.generateSession(clientId, pwd, totp)
# print(data)
authToken = data['data']['jwtToken']
refreshToken = data['data']['refreshToken']

# fetch the feedtoken
feedToken = smartApi.getfeedToken()

# fetch User Profile
res = smartApi.getProfile(refreshToken)
smartApi.generateToken(refreshToken)
res=res['data']['exchanges']



#Historic api
try:
    historicParam={
    "exchange": "NSE",
    "symboltoken": "3045",
    "interval": "FIVE_MINUTE",
    "fromdate": "2021-02-08 09:00", 
    "todate": "2021-02-08 09:30"
    }
    h = smartApi.getCandleData(historicParam)
except Exception as e:
    print("Historic Api failed: {}".format(e.message))
    
    
#logout
# try:
#     logout=smartApi.terminateSession('Your Client Id')
#     print("Logout Successfull")
# except Exception as e:
#     print("Logout failed: {}".format(e.message))