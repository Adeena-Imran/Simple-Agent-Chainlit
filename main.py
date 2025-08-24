import os
from dotenv import load_dotenv
from typing import cast
import chainlit as cl
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")


#from here the chat will be started {FUNCTION OF STARTING THE CHAT SESSION} 
@cl.on_chat_start
async def start():

    #Reference: https://ai.google.dev/gemini-api/docs/openai
    external_client = AsyncOpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    model = OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",
        openai_client=external_client
    )

    config = RunConfig(
        model=model,
        model_provider=external_client,
        tracing_disabled=True
    )

#making an empty list to store the memory of the user
    cl.user_session.set("chat history:",[])
    cl.user_session.set("config", config) #to save the config also

    agent: Agent = Agent(
        name= "Assisstant",
        instructions= "You are a helpful assisstant.",
        model= model
    )

    cl.user_session.set("agent", agent) 
    await cl.Message(content="Welcome to the AI Assisstant. How can I help you?").send()


#FUNCTION OF RECIEVING THE MESSAGE---->when user send any msg then this function runs
@cl.on_message
async def main(message:cl.Message):
    history = cl.user_session.get("chat history") or []
    history.append({"role":"user", "content": message.content}) 

    msg= cl.Message(content="")
    await msg.send()

    agent:Agent = cast(Agent, cl.user_session.get("agent")) 
    config:RunConfig = cast(RunConfig, cl.user_session.get("config"))
    
    try:
        print("/n[CALLING_AGENT_WITH_CONTEXT]/n", history,"/n") 
#now here we run our agent in a streaming mode for line by line response

        result = Runner.run_streamed(agent, history, run_config=config)
        async for event in result.stream_events():
            if event.type == "raw_response_event" and hasattr(event.data, 'delta'):
                token = event.data.delta 
                await msg.stream_token(token)
        #now to store final msg in history
        history.append({"role":"assisstant", "content":msg.content})
        cl.user_session.set("chat_history", history)



      
        print(f"User: {message.content}")
        print(f"Assisstant: {msg.content}") 

    except Exception as e:
     
        await msg.update(content =f"Error: {str(e)}")
        print(f"Error: {str(e)}")






