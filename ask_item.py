import logging
import py_trees
from toolbox import Toolbox
from item_types import ChickenNuggetsItem, HamburgerItem
from llm_node import LLMJob


class AskItem(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)

        self.blackboard = self.attach_blackboard_client(name="Global")
        self.blackboard.register_key(key="current_item", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="llm_job", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="needs_customer_input", access=py_trees.common.Access.WRITE)

    def update(self):
        logging.info(f"Saw update: {self.name}")
        
        user = """
You are an order taker at a take out restaurant.

Find out what the user wants to order, then use the "add_item" tool to start the ordering process.

DON'T ask any questions that you can't fulfill with the tools available to you.
        """
        
        toolbox = Toolbox()
        
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

        job = LLMJob(user=user, toolbox=toolbox, include_history=True)
        self.blackboard.llm_job = job
        self.blackboard.needs_customer_input = True

        return py_trees.common.Status.RUNNING