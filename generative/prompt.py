parent_prompt = \
"""You are assisting a user with a personal information removal request.

Generate a professional suggested takedown request based ONLY
on the information provided below.

...

REQUIREMENTS:
- Clearly identify every verified piece of personal information.
- Include the exact values provided above.
- Clearly identify the source URL.
- Identify the organisation where provided.
- Do not invent any facts.
- Do not claim that a legal violation has definitely occurred.
- Do not threaten legal action.
- Do not include information that is not listed as verified.
- This is a suggested draft and will be reviewed by the user."""