def handle_response(message) -> str:
    
    p_message = message.lower()
    
    print(message)
    
    if p_message == "hello":
        return "hey, I'm the wine bot"
    
    if p_message == "!help":
        return "this would be a help message to help you use this bot"
    

    
    
    