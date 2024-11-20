# Marcos_Mick
Marcos and Mick github repository for 411 summer 2024

### Title:
The Research Overview
### Purpose:
An application for faculty to explore research areas and manage their personal research keywords.
Show users what keyword are popular and illustrate relations between different areas of research.
### Demo:
https://mediaspace.illinois.edu/media/t/1_wzhd14lx
### Installation:
Initial installaion: run database_setup.py once. It establishes mysql views and procedures.
### Usage:
Select a keyword from the table or search for keywords containing a certain word.
The the top keywords and top related keyword will respond with filters available.
Users can look up faculty members and change their information.
Users can look up a faculty member and delete or add a keyword.
In a practical senario, we would have passwords for each faculty member and require them to verify themselves every time they submit a change.
### Implementation:
This dashboard with implimented with Python Dash, Plotly, mySQL, pymongo, and neo4j.
Dash was used for the front end and dbms querying.
Plotly was used for creating the pie charts and bar charts.
### Database Techniques:
We inplimented database views, procedures, and indexes.
We created a mysql view and procedure to simplify simple queries that were often used: reporting keywords.
We implimented an index for keywords in MySQL, MongoDB, and Neo4j. The dashboard queries for keywords so frequently that having an index for keywords justifies the extra space it takes up.
### Extra-Credit Capabilities
This dashboard applies Multi-database querying. After the user's initial keyword mySQL query, the results of that query are used in the MongoDB and Neo4j queries where they retrieve the top keywords, top related keywords, and top related faculty member based on KRC. This feature took 20 hours to create and polish.
### Contributions
Marcos - Widgets: Keyword Table, Search, Piechart, Barchart: 20 hours. Dashboard layout: 1 hour. Database techniques: 2 hours. 
Mick - Widgets: Search, Top Faculty, Faculty Editor, Keyword Add and Delete: 20 hours.  Dashboard layout: 3 hours.
