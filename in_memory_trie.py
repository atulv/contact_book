from threading import Lock

class Slot(object):
    """
        has three fields
        next is the next node
        count is the number of contacts in the subtee
        ids is the list of contact for this slot.
    """
    def __init__(self):
        self.next = None
        self.count = 0
        self.ids = None

class Node(object):
    def __init__(self):
        self.slots = dict()


class Trie(object):
    """
    class implement trie datastructure
    each node is dictionary of char and slots
    """
    def __init__(self):
        self.root = Node()
        self.lock = Lock()

    def insert(self, word, _id):
        """
        inserts word in trie and updates the count for nodes at intestion path
        """
        l = len(word) - 1

        def _insert(node, idx):
            char = word[idx]
            a = 0
            if char in node.slots:
                new_node = node.slots[char]
                if idx < l:
                    if not new_node.next:
                        new_node.next = Node()
                    a = _insert(new_node.next, idx+1)
                else:
                    new_node.count += 1
                    try:
                        new_node.ids.append(_id)
                    except:
                        new_node.ids = [_id]
                    return 1
            else:
                node.slots[char] = Slot()
                if idx < l:
                    new_node = Node()
                    node.slots[char].next = new_node
                    a = _insert(new_node, idx+1)
                else:
                    new_node = node.slots[char]
                    new_node.count += 1
                    try:
                        new_node.ids.append(_id)
                    except:
                        new_node.ids = [_id]
                        return 1
            node.slots[char].count += a
            return a

        node = self.root
        with self.lock:
            _insert(node, 0)

    def delete(self, word, _id):
        """
        deletes only contact ids from slots, does not delete nodes.
        """
        l = len(word) - 1

        def _delete(node, idx):
            char = word[idx]
            try:
                _slot = node.slots[char]
            except:
                return 0

            if idx == l:
                try:
                    _slot.ids.remove(_id)
                    _slot.count -= 1
                    return 1
                except:
                    return 0

            a = 0
            if _slot.next:
                a = _delete(_slot.next, idx+1)

            _slot.count -= a
            return a

        node = self.root
        with self.lock:
            _delete(node, 0)

    def find(self, word, start, count):
        """
        finds all words with prefix as word
        """
        _slot = self.find_exact(word)
        _total = _slot.count
        ret = []
        if _slot.ids:
            if len(_slot.ids) < start:
                start -= len(_slot.ids)
            else:
                ret.extend(_slot.ids[start:start+count])
                count -= len(ret)
                start = 0
        new_node = _slot.next
        se = [start, count]
        def _find(node):
            if not node: return
            if se[1] <=0:
                return

            for k in sorted(node.slots.keys()):
                _slot = node.slots[k]
                if _slot.count < se[0]:
                    se[0] -= _slot.count
                else:
                    if not se[0]:
                        if _slot.ids:
                            if len(_slot.ids) < se[1]:
                                se[1] -= len(_slot.ids)
                                ret.extend(_slot.ids)
                                _find(_slot.next)
                            else:
                                ret.extend(_slot.ids[:se[1]])
                                se[1] = 0
                        else:
                            _find(_slot.next)
                    elif _slot.count == se[0] and not _slot.next:
                        ret.append(_slot.ids[-1])
                        se[1] -= 1
                    else:
                        _find(_slot.next)
        with self.lock:
            _find(new_node)
        return ret
            

    def find_exact(self, word):
        node = self.root
        l = len(word) - 1
        for i, char in enumerate(word):
            try:
                node = node.slots[char]
                if i<l:
                    node = node.next
            except KeyError:
                return None
        return node
            

    def insert2(self, word, _id):
        node = self.root
        for char in word:
            if char in node.slots:
                node = node.slots[char]
            else:
                node.slots[char] = Node()
                node.filled_slots += 1
                node = node.slots[char]
        node.object_ids.add(_id)

    def delete2(self, word, _id):
        node = self.root
        for char in word:
            try:
                node = node.slots[char]
            except KeyError:
                return -1
        node.object_ids.remove(_id)
        return 1


    def find2(self, word):
        node = self.root
        for char in word:
            try:
                node = node.slots[char]
            except KeyError:
                return 0

        return node.object_ids


