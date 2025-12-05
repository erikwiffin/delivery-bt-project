import logging
import py_trees
from toolbox import Toolbox
from llm_node import LLMJob


class AskTopping(py_trees.behaviour.Behaviour):
    def __init__(self, name, topping):
        super().__init__(name)

        self.topping = topping

        self.blackboard = self.attach_blackboard_client(name="Global")
        self.blackboard.register_key(key="current_item", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="llm_job", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="needs_customer_input", access=py_trees.common.Access.WRITE)

    def update(self):
        logging.info(f"Saw update: {self.name}")
        
        toolbox = Toolbox()
        
        @toolbox.function(description=f"Set whether or not this item comes with {self.topping}.")
        @toolbox.parameter("yes", description=f"Do they want {self.topping}?", type="boolean")
        def set_topping(yes: bool):
            if not isinstance(yes, bool):
                raise TypeError(f"{yes} is not a boolean")
            self.blackboard.current_item.__dict__[self.topping] = yes
            self.blackboard.needs_customer_input = False

            return "SUCCESS"

        user = f"""
You are an order taker at a take out restaurant.

The user has asked for {self.blackboard.current_item.name}, now find out if they'd like {self.topping} on that.
If they do, use the "set_topping" tool with yes=True. Otherwise, use "set_topping" with yes=False.

DON'T ask any questions that you can't fulfill with the tools available to you.
        """

        job = LLMJob(user=user, toolbox=toolbox, include_history=True)
        self.blackboard.llm_job = job
        self.blackboard.needs_customer_input = True

        return py_trees.common.Status.RUNNING