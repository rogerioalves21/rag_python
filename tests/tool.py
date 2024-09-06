import ollama


prompt = PromptTemplate(
            template="Você é um assistente jurídico prestativo, respeitoso e honesto. Sua tarefa é auxiliar os advogados na análise de ações e processos.\n{format_instructions}\n{question}\n\n\n### Contexto ###\n\n```{context}```",
            input_variables=["question"],
            partial_variables={"format_instructions": format_instructions, "context": texto},
        )

response = ollama.chat(
    model='kuqoi/qwen2-tools',
    messages=[
      {'role': 'system', 'content': "Você é um assistente jurídico prestativo, respeitoso e honesto. Sua tarefa é auxiliar os advogados na análise de ações e processos.\n{format_instructions}\n{question}\n\n\n### Contexto ###\n\n```{context}```"}
      {'role': 'user', 'content': 'What is the weather in Toronto?'}
    ],

		# provide a weather checking tool to the model
    tools=[{
      'type': 'function',
      'function': {
        'name': 'get_current_weather',
        'description': 'Get the current weather for a city',
        'parameters': {
          'type': 'object',
          'properties': {
            'city': {
              'type': 'string',
              'description': 'The name of the city',
            },
          },
          'required': ['city'],
        },
      },
    },
  ],
)

print(response['message']['tool_calls'])

import sys; sys.exit(0)


import json
import ollama
import asyncio


# Simulates an API call to get flight times
# In a real application, this would fetch data from a live database or API
def get_flight_times(departure: str, arrival: str) -> str:
  flights = {
    'NYC-LAX': {'departure': '08:00 AM', 'arrival': '11:30 AM', 'duration': '5h 30m'},
    'LAX-NYC': {'departure': '02:00 PM', 'arrival': '10:30 PM', 'duration': '5h 30m'},
    'LHR-JFK': {'departure': '10:00 AM', 'arrival': '01:00 PM', 'duration': '8h 00m'},
    'JFK-LHR': {'departure': '09:00 PM', 'arrival': '09:00 AM', 'duration': '7h 00m'},
    'CDG-DXB': {'departure': '11:00 AM', 'arrival': '08:00 PM', 'duration': '6h 00m'},
    'DXB-CDG': {'departure': '03:00 AM', 'arrival': '07:30 AM', 'duration': '7h 30m'},
  }

  key = f'{departure}-{arrival}'.upper()
  return json.dumps(flights.get(key, {'error': 'Flight not found'}))


async def run(model: str):
  client = ollama.AsyncClient()
  # Initialize conversation with a user query
  messages = [{'role': 'user', 'content': 'What is the flight time from New York (NYC) to Los Angeles (LAX)?'}]

  # First API call: Send the query and function description to the model
  response = await client.chat(
    model=model,
    messages=messages,
    tools=[
      {
        'type': 'function',
        'function': {
          'name': 'get_flight_times',
          'description': 'Get the flight times between two cities',
          'parameters': {
            'type': 'object',
            'properties': {
              'departure': {
                'type': 'string',
                'description': 'The departure city (airport code)',
              },
              'arrival': {
                'type': 'string',
                'description': 'The arrival city (airport code)',
              },
            },
            'required': ['departure', 'arrival'],
          },
        },
      },
    ],
  )

  # Add the model's response to the conversation history
  messages.append(response['message'])

  # Check if the model decided to use the provided function
  if not response['message'].get('tool_calls'):
    print("The model didn't use the function. Its response was:")
    print(response['message']['content'])
    return

  # Process function calls made by the model
  if response['message'].get('tool_calls'):
    available_functions = {
      'get_flight_times': get_flight_times,
    }
    for tool in response['message']['tool_calls']:
      function_to_call = available_functions[tool['function']['name']]
      function_response = function_to_call(tool['function']['arguments']['departure'], tool['function']['arguments']['arrival'])
      # Add function response to the conversation
      messages.append(
        {
          'role': 'tool',
          'content': function_response,
        }
      )

  # Second API call: Get final response from the model
  final_response = await client.chat(model=model, messages=messages)
  print(final_response['message']['content'])


# Run the async function
asyncio.run(run('mistral'))