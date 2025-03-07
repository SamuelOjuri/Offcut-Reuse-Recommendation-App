import os
from dotenv import load_dotenv
#from together import Together
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
#from langchain_together import Together
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# Load environment variables from the .env file
load_dotenv()

# TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
# if not TOGETHER_API_KEY:
#     raise ValueError("TOGETHER_API_KEY environment variable is required")

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

#openai.api_key = OPENAI_API_KEY

# client = Together(
#     model="Qwen/Qwen2.5-Coder-32B-Instruct",
#     #model="meta-llama/Meta-Llama-3.3-70B-Instruct-Turbo",
#     #model="nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
#     api_key=TOGETHER_API_KEY,
#     max_tokens=4096
# )

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Initialize database connection with error handling
try:
    db = SQLDatabase.from_uri(DATABASE_URL)
except Exception as e:
    print(f"Error connecting to database: {e}")
    raise

# Initialize LLM with error handling
# try:
#     llm = Together(
#         model="Qwen/Qwen2.5-Coder-32B-Instruct",
#         temperature=0.0,
#         max_tokens=4096,
#         api_key=TOGETHER_API_KEY,
#     )
# except Exception as e:
#     print(f"Error initializing LLM: {e}")
#     raise


# Initialize LLM with OpenAI GPT-4o
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model_name="gpt-4o",  # or gpt-3.5-turbo
    temperature=0.0,
    max_tokens=None,
    )

# Initialize toolkit with error handling
try:
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    toolkit.model_rebuild()
except Exception as e:
    print(f"Error initializing toolkit: {e}")
    raise

tools = toolkit.get_tools()


REACT_TEMPLATE = """You are an agent designed to interact with a PostgreSQL database.
Given an input question, create a syntactically correct PostgreSQL query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.

You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

To start you should ALWAYS look at the tables in the database to see what you can query.
Do NOT skip this step.
Then you should query the schema of the most relevant tables.

You have access to the following tools for interacting with the database:
{tools}
Only use the provided tools. Only use the information returned by these tools to construct your final answer.

To use a tool, please use the following format:
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action

When you have a final answer, you can return it in the following format:
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

# Create the agent with react prompt template
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=PromptTemplate.from_template(REACT_TEMPLATE)
)

# Create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)




def stream_final_answer(prompt):
    for chunk in agent_executor.stream({"input": prompt}):
        if isinstance(chunk, dict) and 'output' in chunk:
            yield chunk['output']
        elif isinstance(chunk, str) and 'Final Answer:' in chunk:
            yield chunk.split('Final Answer:')[1].strip()