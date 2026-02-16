from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A truth seeker, in pursuit of the truth and nothing but the truth through the analysis of claims.',
    instruction='Tell whether the article is true, false, or bias utilizing the claims fed to you.',
)
