import logging
import json
import dataclasses
import py_trees
from toolbox import Toolbox
from llm_node import LLMJob


class ConfirmItem(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)

        self.blackboard = self.attach_blackboard_client(name="Global")
        self.blackboard.register_key(key="current_item", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="order", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="llm_job", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="needs_customer_input", access=py_trees.common.Access.WRITE)

    def update(self):
        logging.info(f"Saw update: {self.name}")

        if self.blackboard.current_item is None:
            return py_trees.common.status.SUCCESS
        
        toolbox = Toolbox()
        
        @toolbox.function()
        @toolbox.parameter("field", description="The field that the user has a problem with", enum=["quantity", "fries"])
        def reset_field(field: str):
            '''
            Change a field on the order item
            '''
            self.blackboard.current_item.__dict__[field] = None
            self.blackboard.needs_customer_input = False

            return "SUCCESS"
            
        @toolbox.function()
        def confirm():
            '''
            Confirm an order item and add it to their final order
            '''
            self.blackboard.order.append(self.blackboard.current_item)
            self.blackboard.current_item = None
            self.blackboard.needs_customer_input = False

            return "CONFIRM"

        user = f"""
You are an order taker at a take out restaurant.

The customer is placing an order for a menu item. Menu items have various customization options and can come with sides.
The user has answered all your questions about a menu item. 

Read back their order, then ask them if there's anything they'd like to change about this item.

If they'd like to change something, use the "reset_field" tool.
If they're good with their order, use the "confirm" tool.

This is the current item in their order:

{json.dumps(dataclasses.asdict(self.blackboard.current_item))}

If something in this item doesn't match the conversation history, you've probably changed the item.

DON'T ask any questions that you can't fulfill with the tools available to you.
        """

        job = LLMJob(user=user, toolbox=toolbox, include_history=True)
        self.blackboard.llm_job = job
        self.blackboard.needs_customer_input = True

        return py_trees.common.Status.RUNNING