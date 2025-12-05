import logging
import py_trees

class CustomerInput(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)

        self.blackboard = self.attach_blackboard_client(name="Global")
        self.blackboard.register_key(key="message_history", access=py_trees.common.Access.WRITE)
        self.blackboard.register_key(key="needs_customer_input", access=py_trees.common.Access.WRITE)

    def update(self):
        logging.info(f"Saw update: {self.name}")

        reply = input()

        self.blackboard.message_history.append({ "role": "user", "content": reply })
        self.blackboard.needs_customer_input = False

        return py_trees.common.Status.SUCCESS