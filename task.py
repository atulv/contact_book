from threading import Thread

class Task(Thread):
    def __init__(self, trie, operation, word, contact_id):
        Thread.__init__(self)
        self.trie = trie
        self.str = word
        self.obj = contact_id
        self.operation = operation

    def run(self):
        if self.operation == 'add':
            self.trie.insert(self.str, self.obj)
        elif self.operation == 'remove':
            self.trie.delete(self.str, self.obj)

        
        
