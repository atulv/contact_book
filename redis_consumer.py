import os, sys                                                   
                                                                                  
os.environ['DJANGO_SETTINGS_MODULE'] = 'contact_book.settings'                          
                                                                                  
ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))                         
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]                               
                                                                                  
if ROOT_FOLDER not in sys.path:                                                   
    sys.path.insert(1, ROOT_FOLDER + '/')                                         
                                                                                  
from django.conf import settings 
from task import Task
from threading import BoundedSemaphore
from apis import views
redis_connection = settings.REDIS_CONNECTION
name_trie = views.name_trie
email_trie = views.email_trie
queue = settings.REDIS_QUEUE
thread_pool = BoundedSemaphore(2)

while True:
    _, item = redis_connection.blpop(queue)
    action, task_type, word, _id = eval(item)
    if task_type == 0:
        task = Task(email_trie, action, word, _id)
    else:
        task = Task(name_trie, action, word, _id)
    thread_pool.acquire()
    task.start()
    thread_pool.release()
