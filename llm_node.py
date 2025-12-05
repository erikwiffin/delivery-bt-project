import logging
import re
import dataclasses

import py_trees
from toolbox import Toolbox

@dataclasses.dataclass
class LLMJob:
    system: str | None = None
    user: str | None = None
    toolbox: Toolbox | None = None
    include_history: bool = False

def extract_reasoning(text):
    if text is None:
        return None, None
    # Pattern looks for [THINK], captures everything until [/THINK], 
    # and then captures everything after.
    # re.DOTALL allows the (.) to match newlines.
    pattern = r"\[THINK\](.*?)\[/THINK\](.*)"
    
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        reasoning = match.group(1).strip() # .strip() removes leading/trailing whitespace
        content = match.group(2).strip()
        return reasoning, content
    else:
        # If no tags are found, return None for reasoning and the original text
        return None, text


def format_message(message):
    if "reasoning" in message:
        return { "role": message["role"], "content": f"[THINK]{message['reasoning']}[/THINK]{message['content']}" }
    else:
        return message


class LLMNode(py_trees.behaviour.Behaviour):
    def __init__(self, name, client):
        super().__init__(name)

        self.client = client

        self.jobs = []
        self.last_message = None

        self.blackboard = self.attach_blackboard_client(name=f"LLNode: {name}")
        self.blackboard.register_key(key="message_history", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="needs_customer_input", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="llm_job", access=py_trees.common.Access.WRITE)

    def update(self):
        logging.info(f"Saw update: {self.name}")

        job = self.blackboard.llm_job

        messages = []
        if job.system:
            messages.append({ "role": "system", "content": job.system })
        if job.user:
            content = job.user
            if job.include_history:
                history = "\n".join([f'{message["role"]}: {message["content"]}' for message in self.blackboard.message_history])
                content = f"""
{content}

---
Conversation History:

{history}
"""
            messages.append({ "role": "user", "content": content })

        logging.info(messages)

        response = self.client.chat.completions.create(
            model="gemini-3-pro-preview",
            messages=messages,
            tools=job.toolbox.tools if job.toolbox else None,
            temperature=0.1,
        )
        
        job.toolbox.execute(response.choices[0].message)
        text = response.choices[0].message.content
        reasoning, content = extract_reasoning(text)

        self.last_message = response.choices[0].message

        if content and content != "":
            if reasoning:
                self.blackboard.message_history.append({ "role": "assistant", "content": content, "reasoning": reasoning })
            else: 
                self.blackboard.message_history.append({ "role": "assistant", "content": content })

        self.blackboard.llm_job = None
        self.jobs.append(job)

        return py_trees.common.Status.SUCCESS