import py_trees
import logging
import json
import dataclasses
from toolbox import Toolbox
from llm_node import LLMJob

class AskFries(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)

        self.blackboard = self.attach_blackboard_client(name="Global")
        self.blackboard.register_key(key="current_item", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="llm_job", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="needs_customer_input", access=py_trees.common.Access.WRITE)

    def update(self):
        logging.info(f"Saw update: {self.name}")
        
        toolbox = Toolbox()
        
        @toolbox.function()
        @toolbox.parameter("fries", description="Do they want fries with that?", type="boolean")
        def set_fries(fries: bool):
            '''
            Set whether or not this item comes with fries.
            '''
            if not isinstance(fries, bool):
                raise TypeError(f"{fries} is not a boolean")
            self.blackboard.current_item.fries = fries
            self.blackboard.needs_customer_input = False

            return "SUCCESS"

        user = f"""
You are an order taker at a take out restaurant.

The user has asked for an item, now find out if they'd like fries with that,
then use the "set_fries" tool to save that information.

This is what we know about the current item:
{json.dumps(dataclasses.asdict(self.blackboard.current_item))}

DON'T ask any questions that you can't fulfill with the tools available to you.
        """

        job = LLMJob(user=user, toolbox=toolbox, include_history=True)
        self.blackboard.llm_job = job
        self.blackboard.needs_customer_input = True

        return py_trees.common.Status.RUNNING