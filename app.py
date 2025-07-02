# ✅ Natural Language to SQL Streamlit App for AdventureWorks DB using LangChain

import os
from operator import itemgetter
from typing import List
import pandas as pd
import streamlit as st

from langchain.chains import create_sql_query_chain
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.memory import ChatMessageHistory
from langchain_community.vectorstores import Chroma
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import FewShotChatMessagePromptTemplate

# ========== 🔐 CONFIG ==========
# ⛔ REPLACE WITH YOUR ACTUAL KEYS & DB INFO
os.environ["OPENAI_API_KEY"] = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
db_user = "admin"  # or whatever you used when creating the DB
db_password = "Shanuk200206"
db_host = "adventureworks.xxxxxxxxxxx.us-east-1.rds.amazonaws.com"  # copy from RDS dashboard
db_name = "adventureworks"

# ========== 🗃️ DATABASE ==========
db = SQLDatabase.from_uri(
    "mysql+pymysql://admin:xxxxxxxxxx@adventureworks.xxxxxxxxxx.us-east-1.rds.amazonaws.com/adventureworks"
)


# ========== 🗣️ LLM ==========
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# ========== 📋 FEW-SHOT EXAMPLES ==========
examples = [
    {
        "input": "List all employees in the Sales department.",
        "query": "SELECT p.FirstName, p.LastName FROM HumanResources.Employee e JOIN HumanResources.EmployeeDepartmentHistory edh ON e.BusinessEntityID = edh.BusinessEntityID JOIN HumanResources.Department d ON edh.DepartmentID = d.DepartmentID JOIN Person.Person p ON e.BusinessEntityID = p.BusinessEntityID WHERE d.Name = 'Sales';"
    },
    {
        "input": "What is the highest product list price?",
        "query": "SELECT MAX(ListPrice) FROM Production.Product;"
    },
    {
        "input": "How many customers are from Canada?",
        "query": "SELECT COUNT(*) FROM Sales.Customer c JOIN Person.Person p ON c.PersonID = p.BusinessEntityID JOIN Person.Address a ON p.BusinessEntityID = a.AddressID WHERE a.CountryRegion = 'Canada';"
    }
]

example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}\nSQLQuery:"),
    ("ai", "{query}")
])

vectorstore = Chroma.from_texts(
    texts=[ex["input"] for ex in examples],
    embedding=OpenAIEmbeddings(),
    metadatas=[{"query": ex["query"]} for ex in examples],
    collection_name="example_selector"
)

example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    OpenAIEmbeddings(),
    vectorstore,
    k=2,
    input_keys=["input"]
)

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    example_selector=example_selector,
    input_variables=["input"]
)

# ========== 📚 TABLE DESCRIPTIONS ==========
def get_table_details():
    table_description = pd.read_csv("database_table_descriptions.csv")
    table_details = ""
    for _, row in table_description.iterrows():
        table_details += f"Table Name: {row['Table']}\nTable Description: {row['Description']}\n\n"
    return table_details

table_details = get_table_details()

# ========== 🔹 TABLE SELECTION PROMPT ==========
class Table(BaseModel):
    name: str = Field(description="Name of table in SQL database.")

table_selection_prompt = PromptTemplate(
    input_variables=["input", "table_info", "top_k"],
    template="""Return the names of ALL the SQL tables that MIGHT be relevant to the user question.

Here is the user question:
{input}

Here is the table info:
{table_info}

(top_k = {top_k}) — You can ignore this if not needed.

Remember to include ALL POTENTIALLY RELEVANT tables, even if you're not sure that they're needed."""
)

def get_tables(tables: List[Table]) -> List[str]:
    return [table.name for table in tables]

select_table = (
    {
        "input": itemgetter("question"),
        "table_info": lambda _: table_details,
        "top_k": lambda _: 5
    } |
    create_sql_query_chain(llm, db, table_selection_prompt) |
    get_tables
)

# ========== 🔧 SQL GENERATION ==========
sql_query_prompt = PromptTemplate.from_template(
    """Given the following question, table info, and top_k value, write a syntactically correct MySQL query to answer the question.\n\nQuestion: {input}\nTop K: {top_k}\nTable Info:\n{table_info}\n\nSQL Query:"""
)

# ========== 🔎 ANSWER REPHRASING ==========
answer_prompt = PromptTemplate.from_template(
    """Given the following user question, corresponding SQL query, and SQL result, answer the user question.

Question: {question}
SQL Query: {query}
SQL Result: {result}
Answer:"""
)
rephrase_answer = answer_prompt | llm | StrOutputParser()

# ========== 🧠 MEMORY ==========
if "history" not in st.session_state:
    st.session_state.history = ChatMessageHistory()
history = st.session_state.history

# ========== 🛠️ FINAL CHAIN ==========
generate_query = create_sql_query_chain(llm, db, sql_query_prompt)
from langchain.tools.sql_database.tool import QuerySQLDataBaseTool

execute_query = QuerySQLDataBaseTool(db=db)

chain = (
    RunnablePassthrough.assign(table_names_to_use=select_table) |
    RunnablePassthrough.assign(query=generate_query).assign(
        result=itemgetter("query") | execute_query
    ) |
    rephrase_answer
)

# ========== 🚀 STREAMLIT UI ==========
st.set_page_config(page_title="AdventureWorks NL2SQL", layout="centered")
st.title("\ud83d\udcca Ask AdventureWorks Database")

question = st.text_input("Ask a question:", placeholder="e.g., List employees in the Marketing department")

if question:
    with st.spinner("Thinking..."):
        try:
            response = chain.invoke({"question": question, "messages": history.messages})
            st.success(response)

            history.add_user_message(question)
            history.add_ai_message(response)
        except Exception as e:
            st.error(f"\u274c Error: {str(e)}")

