from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.prompts import SemanticSimilarityExampleSelector
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import FewShotPromptTemplate
from langchain.chains.sql_database.prompt import PROMPT_SUFFIX
from langchain.prompts.prompt import PromptTemplate


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set the timeout configuration for your Flask app
app.config["TIMEOUT"] = 120  # 120 seconds (2 minutes)


@app.route("/api/query", methods=["POST"])
def process_query():
    try:
        query = request.json.get("question")
        if not query:
            return jsonify({"error": "Query not provided"}), 400

        result = execute_query(query)

        # Assuming result is a string, you can modify this based on the actual output format
        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def execute_query(query):
    api_key = "AIzaSyBjY0ha4rcAZ2cfcFjUe_e3i0t6FZpyVxo"
    llm = GoogleGenerativeAI(
        model="models/text-bison-001", google_api_key=api_key, temperature=0.2
    )

    db_user = "root"
    db_password = "root"
    db_host = "localhost"
    db_name = "atliq_tshirts"

    db = SQLDatabase.from_uri(
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}",
        sample_rows_in_table_info=3,
    )
    db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)

    qns1 = db_chain.run(
        "How many t-shirts do we have left for nike in extra small size and white color?"
    )

    qns2 = db_chain.run(
        "SELECT SUM(price*stock_quantity) FROM t_shirts WHERE size = 'S'"
    )

    sql_code = """
    select sum(a.total_amount * ((100-COALESCE(discounts.pct_discount,0))/100)) as total_revenue from
    (select sum(price*stock_quantity) as total_amount, t_shirt_id from t_shirts where brand = 'Levi'
    group by t_shirt_id) a left join discounts on a.t_shirt_id = discounts.t_shirt_id
    """

    qns3 = db_chain.run(sql_code)

    qns4 = db_chain.run(
        "SELECT SUM(price * stock_quantity) FROM t_shirts WHERE brand = 'Levi'"
    )
    qns5 = db_chain.run(
        "SELECT sum(stock_quantity) FROM t_shirts WHERE brand = 'Levi' AND color = 'White'"
    )

    few_shots = [
        {
            "Question": "How many t-shirts do we have left for Nike in XS size and white color?",
            "SQLQuery": "SELECT sum(stock_quantity) FROM t_shirts WHERE brand = 'Nike' AND color = 'White' AND size = 'XS'",
            "SQLResult": "Result of the SQL query",
            "Answer": qns1,
        },
        {
            "Question": "How much is the total price of the inventory for all S-size t-shirts?",
            "SQLQuery": "SELECT SUM(price*stock_quantity) FROM t_shirts WHERE size = 'S'",
            "SQLResult": "Result of the SQL query",
            "Answer": qns2,
        },
        {
            "Question": "If we have to sell all the Levi’s T-shirts today with discounts applied. How much revenue  our store will generate (post discounts)?",
            "SQLQuery": """SELECT sum(a.total_amount * ((100-COALESCE(discounts.pct_discount,0))/100)) as total_revenue from
            (select sum(price*stock_quantity) as total_amount, t_shirt_id from t_shirts where brand = 'Levi'
            group by t_shirt_id) a left join discounts on a.t_shirt_id = discounts.t_shirt_id
            """,
            "SQLResult": "Result of the SQL query",
            "Answer": qns3,
        },
        {
            "Question": "If we have to sell all the Levi’s T-shirts today. How much revenue our store will generate without discount?",
            "SQLQuery": "SELECT SUM(price * stock_quantity) FROM t_shirts WHERE brand = 'Levi'",
            "SQLResult": "Result of the SQL query",
            "Answer": qns4,
        },
        {
            "Question": "How many white color Levi's shirt I have?",
            "SQLQuery": "SELECT sum(stock_quantity) FROM t_shirts WHERE brand = 'Levi' AND color = 'White'",
            "SQLResult": "Result of the SQL query",
            "Answer": qns5,
        },
    ]

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    to_vectorize = [" ".join(example.values()) for example in few_shots]
    vectorstore = Chroma.from_texts(
        to_vectorize, embedding=embeddings, metadatas=few_shots
    )

    example_selector = SemanticSimilarityExampleSelector(
        vectorstore=vectorstore,
        k=2,
    )
    example_selector.select_examples(
        {"Question": "How many Adidas T shirts I have left in my store?"}
    )

    mysql_prompt = """You are a MySQL expert. Given an input question, first create a syntactically correct MySQL query to run, then look at the results of the query and return the answer to the input question.
    Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL. You can order the results to return the most informative data in the database.
    Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.
    Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
    Pay attention to use CURDATE() function to get the current date, if the question involves "today".

    Use the following format:

    Question: Question here
    SQLQuery: Query to run with no pre-amble
    SQLResult: Result of the SQLQuery
    Answer: Final answer here

    No pre-amble.
    """

    example_prompt = PromptTemplate(
        input_variables=[
            "Question",
            "SQLQuery",
            "SQLResult",
            "Answer",
        ],
        template="\nQuestion: {Question}\nSQLQuery: {SQLQuery}\nSQLResult: {SQLResult}\nAnswer: {Answer}",
    )

    few_shot_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix=mysql_prompt,
        suffix=PROMPT_SUFFIX,
        input_variables=[
            "input",
            "table_info",
            "top_k",
        ],  # These variables are used in the prefix and suffix
    )

    new_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True, prompt=few_shot_prompt)

    result = new_chain(query)

    return result


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")  # Run the Flask app in debug mode
