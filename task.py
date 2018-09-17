from threading import Thread

class Task(Thread):
    def __init__(self, trie, operation, word, contact_id):
        self.trie = trie
        self.str_to_add = word
        self.object_to_add = contact_id
        self.operation = operation
        Thread.__init__(self)

    def run(self):
        if operation == 'add':
            self.trie.insert(self.word, self.contact_id)
        elif operation == 'remove':
            self.trie.delete(self.word, self.contact_id)

    

        
        
