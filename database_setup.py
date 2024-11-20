# this file is supposed to run once.
# Running this file again will just end in errors
# If this file needs to be redone or edited,
# We need to delete the views and procedures this file has already set up in mysql or other dbms

#imports 
import mysql.connector
import pymongo
import neo4j


# connecting to databases

# # MySQL
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="test_root",
    database="academicworld"
)

# setting up views
query = "Create view All_Keywords as SELECT distinct name FROM keyword"
mycursor = mydb.cursor()
mycursor.execute(query)
mycursor.close()
# setting up preocedure
query = """
CREATE PROCEDURE SelectALLKeywords()
BEGIN
    SELECT * FROM All_Keywords;
END;
"""
mycursor = mydb.cursor()
mycursor.execute(query, multi=True)
mycursor.close()
# creating index for keywords
query = "CREATE INDEX keyword_idx ON keyword(name)"
mycursor = mydb.cursor()
mycursor.execute(query)
mycursor.close()


# mymongo setting up keyword index
mongoDB_connect_string = "mongodb://localhost:27017/"
mongoDB_client = pymongo.MongoClient(mongoDB_connect_string)
mongoDB_database = mongoDB_client['academicworld']

mongoDB_database["faculty"].create_index("keyword.name", name="keyword_idx_faculty")
mongoDB_database["publications"].create_index("keyword.name", name="keyword_idx_pub")

# marcos's neo4j login credentials
URI1 = "bolt://localhost:7687"
AUTH1 = ("neo4j", "test_root")
# mick's neo4j login credentials
URI2 = "bolt://localhost:7687"
AUTH2 = ("neo4j", "test_root")
with neo4j.GraphDatabase.driver(URI1,auth=AUTH1) as driver:
    driver.verify_connectivity()
driver = neo4j.GraphDatabase.driver(URI1,auth=AUTH1)
clause = "CREATE INDEX keyword_idx FOR (k:KEYWORD) ON (k.name)"
driver.execute_query(
        clause,
        database_="academicworld",
    )