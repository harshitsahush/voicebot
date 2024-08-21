from crewai import Task

class ChatbotTasks():
    def process_query(agent):
        return Task(
            description = """Analyze and decide whether to search the web for the query results or to search the query answers in the pdf or to get the information from the database. Make sure to provide as accurate results as you can. 
            Query = {query}""",
            agent = agent,
            expected_output = """A detailed response for the given query."""
        )
