# NL_to_SQL
A RAG-based chatbot using LangChain and Streamlit
This project is a Natural Language to SQL (NL2SQL) app that lets users query the AdventureWorks database using plain English — no SQL knowledge required.

It's built using:

🧠 LangChain for prompt chaining and SQL generation

🗃️ MySQL (AWS RDS) for hosting the AdventureWorks database

🧩 Streamlit for a clean interactive UI

🦾 OpenAI GPT-3.5 Turbo for language understanding and SQL output

🧰 Features
✅ Dynamic Table Selection using LLM-based parsing of table descriptions

✅ Semantic Few-Shot Prompting using vector search (Chroma + OpenAI embeddings)

✅ Conversational Memory to handle follow-up questions

✅ Answer Rephrasing for user-friendly responses

✅ Streamlit UI to type questions like:

"How many customers placed more than 5 orders?"

"List employees in the Marketing department"

"Show the highest product price"

🏗️ Tech Stack
Layer	Technology
Backend LLM	OpenAI GPT-3.5 Turbo
Prompt Engine	LangChain
Database	MySQL on AWS RDS
UI	Streamlit
Hosting	AWS EC2

🚧 Current Status
⚠️ This app is currently offline.

The underlying EC2 instance and RDS database are shut down to minimize AWS usage while not in active development.

To reactivate:

Start the EC2 instance (used to host the Streamlit app)

Start the RDS MySQL instance (which hosts the AdventureWorks database)

SSH into EC2 and run:

bash
Copy
Edit
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Open http://<your-ec2-ip>:8501 in your browser

📁 Project Structure
bash
Copy
Edit
.
├── app.py                          # Main Streamlit application
├── requirements.txt               # All dependencies
├── database_table_descriptions.csv  # Table metadata for dynamic prompts
└── README.md
💡 Sample Questions
text
Copy
Edit
• List all products with a list price over 500
• How many orders were placed in 2023?
• Which departments have the most employees?
• What’s the highest payment received?
🔐 Setup Instructions (if rehosting)
Clone the repo on your EC2 instance

Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Make sure your .csv and OPENAI_API_KEY are correctly placed/set

Update app.py with your actual RDS credentials

Launch the app:

bash
Copy
Edit
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
