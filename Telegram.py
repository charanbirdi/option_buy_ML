#https://my.telegram.org/auth?to=apps
#https://my.telegram.org/apps

import asyncio
from telethon import TelegramClient

api_id = '11107636'
api_hash = 'ca1860543e70b59d80047a7929336e8c'
#token = '6638908793:AAEmTejc_1yTea7T7xIP8842d0vU6PKRY6U'

client = TelegramClient('None', api_id, api_hash)


def telegram_message(message):
    async def main(message):
        # await client.send_message('me', 'Hello to myself Charan') 
        # me in above is for sending messages to saved messages       

        await client.send_message('@birdi_angelone_bot', message)
        await asyncio.sleep(2)
    
    with client:
        
        #print("XXXXXXXXXXXXXXXXXXXXXXX")
        #client.log_out()
        #print(client.session.list_sessions())
        client.loop.run_until_complete(main(message))



#with client:
#    asyncio.create_task((main()))





# Experiment to run asyncio inside SPYDER
# import asyncio

# async def fn():
#   print('hello')
#   await asyncio.sleep(5)
#   print('world')

# # asyncio.run(fn()) is not working and gave below error
# # TO avoid RuntimeError: asyncio.run() cannot be called from a running event loop, we use as below:
# asyncio.create_task(fn())









#await main()
#asyncio.run(main())

#client.disconnect()

# async def main():
#     # Most of your code should go here.
#     # You can of course make and use your own async def (do_something).
#     # They only need to be async if they need to await things.
#     async with client.start():
        
#     #async with client.connect():
#         me = await client.get_me()
#         #await do_something(me)
        
#         print(me.username)

# asyncio.run(main())
# #await main()


# async def do_something():
    
#     # in case of script ran first time it will
#     # ask either to input token or otp sent to
#     # number or sent or your telegram id
#     if not client.is_user_authorized():
#     	client.send_code_request(phone)	
#     	# signing in the client
#     	client.sign_in(phone, input('Enter the code: '))
#     try:
#     	# receiver user_id and access_hash, use
#     	# my user_id and access_hash for reference
#     	receiver = InputPeerUser('user_id', 'user_hash')
#     	# sending message using telegram client
#     	client.send_message(receiver, message, parse_mode='html')
#     except Exception as e:	
#     	# there may be many error coming in while like peer
#     	# error, wrong access_hash, flood_error, etc
#     	print(e);

# # disconnecting the telegram session
# #client.disconnect()