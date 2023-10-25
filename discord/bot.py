import discord
import responses 

async def send_message(message, user_message, is_private):
    try:
        response = responses.handle_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)
        
def run_discord_bot():
    TOKEN = 'MTE2NjA5NzA2Mzg3NzAzODA5MA.GOrbdP.eCtvGOLra4qL_OiBi73SxGXo8frWvQSQs5AiVQ'
    # client = discord.Client(intents=discord.Intents.default())
    intents = discord.Intents(messages=True, guilds=True)
    # intents = discord.Intents.default()
    # intents.message_content = True
    # client = discord.Client(intents=intents)
    # intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user} is now running') 
        
    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        username = str(message.author)
        user_message=str(message.content)
        channel=str(message.channel)
        
        print(f"{username}"+" said: "+{user_message}+" ({channel})" )
        
    client.run(TOKEN)
    
    
    
                
    
    