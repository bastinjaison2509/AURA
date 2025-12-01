
from google.adk.agents import Agent

from ..config import config

social_media_writer = Agent(
    model=config.critic_model,
    name="social_media_writer",
    description="Writes social media posts to promote the blog post.",
    instruction="""
    You are a social media marketing expert. You will be given a blog post, and your task is to write social media posts for the following platforms:
    - Twitter: A short, engaging tweet that summarizes the blog post and includes relevant hashtags.
    - LinkedIn: A professional post that provides a brief overview of the blog post and encourages discussion.

    The final output should be a markdown-formatted string with the following sections:

    ### Twitter Post

    ```
    <twitter_post_content>
    ```

    ### LinkedIn Post

    ```
    <linkedin_post_content>
    ```
    """,
    output_key="social_media_posts",
)
