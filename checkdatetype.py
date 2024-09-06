import datetime

#date_int = "20230301"
#date_obj = datetime.datetime.strptime(date_int, '%Y%m%d')
#print(date_obj.date())


date_int = "17SEP2024"
date_obj = datetime.datetime.strptime(date_int, '%d%b%Y')
print(date_obj.date())