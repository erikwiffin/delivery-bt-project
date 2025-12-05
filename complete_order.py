import logging
import json
import dataclasses

import py_trees
from toolbox import Toolbox

from item_types import ChickenNuggetsItem, HamburgerItem
from llm_node import LLMJob


class CompleteOrder(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)

        self.blackboard = self.attach_blackboard_client(name="Global")
        self.blackboard.register_key(key="order", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="llm_job", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="needs_customer_input", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="order_complete", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="current_item", access=py_trees.common.Access.WRITE)

    def update(self):
        logging.info(f"Saw update: {self.name}")
        if self.blackboard.order_complete:
            return py_trees.common.status.SUCCESS
        
        toolbox = Toolbox()
        
        @toolbox.function()
        def complete_order():
            '''
            Complete the order.
            '''
            self.blackboard.order_complete = True
            self.blackboard.needs_customer_input = False

            return "SUCCESS"
        
        @toolbox.function()
        @toolbox.parameter("item_name", description="Which item to start ordering", enum=["chicken nuggets", "hamburger"])
        def add_item(item_name: str):
            '''
            Start the process of ordering an item.
            '''
            if item_name == "chicken nuggets":
                self.blackboard.current_item = ChickenNuggetsItem(name=item_name)
            elif item_name == "hamburger":
                self.blackboard.current_item = HamburgerItem(name=item_name)
            else:
                raise Exception(f"Unrecognized item: {item_name}")
            self.blackboard.needs_customer_input = False

            return "SUCCESS"
        
        user = f"""
You are an order taker at a take out restaurant.

The customer is placing an order.
They've just finished describing an item and adding it to their order.
Now it's time to ask if they'd like to order something else.

These are the items in their order:

{[json.dumps(dataclasses.asdict(item)) for item in self.blackboard.order]}

Read back their order, then ask them if they're finished or if there's something they'd like to add.
Don't suggest anything that is available to order with the "add_item" tool.

If they're good with their order, use the "complete_order" tool.
If they'd like to add something to their order, use the "add_item" tool.

MAKE SURE TO CONFIRM THE ENTIRE ORDER before using "complete_order".

DON'T ask any questions that you can't fulfill with the tools available to you.
        """

        job = LLMJob(user=user, toolbox=toolbox, include_history=True)
        self.blackboard.llm_job = job
        self.blackboard.needs_customer_input = True

        return py_trees.common.Status.RUNNING