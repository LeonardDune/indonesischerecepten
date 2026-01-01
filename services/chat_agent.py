from langchain_neo4j import Neo4jChatMessageHistory
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain.schema import StrOutputParser

from llm import llm
from services.neo4j import get_neo4j_service
from tools.vector import get_recipe
from tools.cypher import cypher_qa
from utils import get_session_id

# Re-use existing tools, but ensure they use the singleton graph if needed
# Note: existing tools might import 'graph' from 'graph.py', which we want to deprecate.
# Ideally we pass our service's graph to them, but for now we rely on their imports.
# We will just focus on wrapping the agent logic here.

def get_recipe_chat_chain():
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Je ben een recepten-expert die informatie over recepten kan geven."),
            ("human", "{input}"),
        ]
    )
    return chat_prompt | llm | StrOutputParser()

def get_agent_tools():
    recipe_chat = get_recipe_chat_chain()
    
    return [
        Tool.from_function(
            name="Algemene chat",
            description="Voor algemene informatie over recepten, ingrediënten en bereidingswijzen. Gebruik dit als de gebruiker een vraag stelt die niet over het zoeken naar specifieke recepten gaat.",
            func=recipe_chat.invoke,
        ), 
        Tool.from_function(
            name="Recepten Search",  
            description="Gebruik dit voor natuurlijk taalonderzoek (bijv. 'recepten met kip en kokos'). Ideaal voor het vinden van algemene recepten op basis van beschrijvingen.",
            func=get_recipe, 
        ),
        Tool.from_function(
            name="Recepten informatie via Cypher",
            description="CRITIEK: Gebruik dit voor complexe verzoeken met categorieën, regio's, aantallen of 'per categorie' vereisten (bijv. '2 recepten per regio voor Bali en Java'). Dit is vereist voor hoge precisie bij gestructureerde gegevens.",
            func = cypher_qa
        )
    ]

def get_memory(session_id):
    neo4j_service = get_neo4j_service()
    return Neo4jChatMessageHistory(session_id=session_id, graph=neo4j_service.graph)



def initialize_agent():
    tools = get_agent_tools()
    
    agent_prompt = PromptTemplate.from_template("""
    Je bent een expert op het gebied van Aziatische recepten. 
    Wees zo hulpvaardig mogelijk en geef zoveel mogelijk informatie over de recepten terug als mogelijk.
    Geef geen antwoord op vragen die niet zijn gerelateerd aan recepten, ingrediënten, bereidingswijzen, kookmethoden of landen en regio's van herkomst van de recepten.
    
    CRITICAL: Let goed op het LAND en de REGIO van het recept in de context. Als de gebruiker vraagt om een Indonesisch recept, geef dan GEEN Thais recept, tenzij er echt niets anders is.
    REGIO's zijn vaak opgeslagen als kleine letters in de context (bijv. 'bali', 'sumatra', 'jakarta', 'aceh', 'sunda', 'madoera').
    
    Geef geen antwoord op basis van je pre-trained knowledge, gebruik alleen de context die je hebt ontvangen.
    
    Voor complexe vragen zoals 'geef me 2 recepten per regio voor X en Y', gebruik ALTIJD de "Recepten informatie via Cypher" tool voor de beste resultaten.
    
    TOOLS:
    ------
    You have access to the following tools:
    
    {tools}
    
    To use a tool, please use the following format:
    
    ```
    Thought: Do I need to use a tool? Yes
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ```
    
    When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:
    
    ```
    Thought: Do I need to use a tool? No
    Final Answer: [your response here]
    ```
    
    CRITICAL: Output ONLY the requested format starting with "Thought:". Do not add any conversational text, pleasantries, or extra comments before or after the block. 
    
    Begin!
    
    Previous conversation history:
    {chat_history}
    
    New input: {input}
    {agent_scratchpad}
    """)
    
    agent = create_react_agent(llm, tools, agent_prompt)
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    
    chat_agent = RunnableWithMessageHistory(
        agent_executor,
        get_memory,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    
    return chat_agent

# Singleton to avoid recreating agent
_chat_agent_instance = None

def get_chat_agent():
    global _chat_agent_instance
    if _chat_agent_instance is None:
        _chat_agent_instance = initialize_agent()
    return _chat_agent_instance

def generate_response(user_input):
    agent = get_chat_agent()
    response = agent.invoke(
        {"input": user_input},
        {"configurable": {"session_id": get_session_id()}},
    )
    return response['output']
