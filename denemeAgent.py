import Agent

agent = Agent.Agent("Trivia Assistant", "You are a helpful assistant that can answer questions about trivia. Only answer in Turkish.")

print(agent.role)
print(agent.generate_response("What is the capital of France?.Tell me about the city"))
