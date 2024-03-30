import json
from openai import OpenAI

client = OpenAI()


# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(location, unit="celsius"):
    """Get the current weather in a given location"""
    weather_info = {
        "location": location,
        "temperature": "22",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    return json.dumps(weather_info)


def run():
    # Step 1: specify any available functions that the model can use
    # https://platform.openai.com/docs/api-reference/chat/create#functions

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    # Step 2: send the conversation and available functions to GPT
    messages = [{"role": "user", "content": "What's the weather like in Budapest?"}]
    first_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )

    print(first_response)
    print()

    first_response_message = first_response.choices[0].message

    # Step 3: check if GPT wanted to call a function
    # https://platform.openai.com/docs/api-reference/chat/create#messages-function_call
    tool_calls = first_response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_current_weather": get_current_weather,
        }  # only one function in this example, but you can have multiple
        messages.append(first_response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                location=function_args.get("location"),
                unit=function_args.get("unit"),
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        second_response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
        )  # get a new response from the model where it can see the function response
        

        print(second_response)
        print()
        print(second_response.choices[0].message.content)


if __name__ == "__main__":
    run()
