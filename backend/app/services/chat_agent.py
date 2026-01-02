from langchain_neo4j import Neo4jChatMessageHistory
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain.schema import StrOutputParser

from ..llm import llm
from .neo4j import get_neo4j_service
from ..tools.vector import get_recipe
from ..tools.cypher import cypher_qa

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
    Je bent de SpiceRoute Assistant, een wereldwijde culinaire expert. 
    Wees zo hulpvaardig mogelijk en geef gedetailleerde informatie over recepten, ingrediënten en culturele achtergronden.
    Geef geen antwoord op vragen die niet zijn gerelateerd aan koken, recepten, ingrediënten of culinaire tradities.
    
    CRITICAL: Let goed op de specifieke KEUKEN (Cuisine) en REGIO uit de context. Beantwoord vragen met precisie op basis van de verstrekte data.
    
    Geef geen antwoord op basis van je algemene voorkennis, gebruik ALTIJD de context die je via de tools hebt ontvangen voor specifieke receptgegevens.
    
    Voor complexe vragen zoals 'geef me 2 recepten per keuken voor Thailand en Indonesië', gebruik ALTIJD de "Recepten informatie via Cypher" tool.
    
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

_chat_agent_instance = None

def get_chat_agent():
    global _chat_agent_instance
    if _chat_agent_instance is None:
        _chat_agent_instance = initialize_agent()
    return _chat_agent_instance

def generate_response(user_input, session_id):
    agent = get_chat_agent()
    response = agent.invoke(
        {"input": user_input},
        {"configurable": {"session_id": session_id}},
    )
    return response['output']
