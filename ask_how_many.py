import logging
import py_trees
from toolbox import Toolbox
from llm_node import LLMJob


class AskHowMany(py_trees.behaviour.Behaviour):
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
        @toolbox.parameter("quantity", description="How many to order")
        def set_quantity(quantity: int):
            '''
            Set the quantity of the item being ordered.
            '''
            self.blackboard.current_item.quantity = quantity
            self.blackboard.needs_customer_input = False

            return "SUCCESS"

        user = """
You are an order taker at a take out restaurant.

The customer has asked for an item, now find out how many of that item they'd like.
Then use the "set_quantity" tool to save that information.

If the customer has already stated exactly how many they'd like, you can use "set_quantity", but don't guess or assume.

DON'T ask any questions that you can't fulfill with the tools available to you.
        """

        job = LLMJob(user=user, toolbox=toolbox, include_history=True)
        self.blackboard.llm_job = job
        self.blackboard.needs_customer_input = True

        return py_trees.common.Status.RUNNING