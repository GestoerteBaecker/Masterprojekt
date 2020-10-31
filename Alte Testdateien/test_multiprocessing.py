import multiprocessing

#https://stackoverflow.com/questions/42651798/start-multiprocessing-process-of-method-in-class-from-init

# WICHTIG: https://stackoverflow.com/questions/29009790/python-how-to-do-multiprocessing-inside-of-a-class

"""
import random
import multiprocessing


def list_append(count, id, out_list):
    """
    Creates an empty list and then appends a
    random number to the list 'count' number
    of times. A CPU-heavy operation!
    """
    for i in range(count):
        out_list.append(random.random())

if __name__ == "__main__":
    size = 10000000   # Number of random numbers to add
    procs = 2   # Number of processes to create

    # Create a list of jobs and then iterate through
    # the number of processes appending each process to
    # the job list 
    jobs = []
    for i in range(0, procs):
        out_list = list()
        process = multiprocessing.Process(target=list_append, 
                                          args=(size, i, out_list))
        jobs.append(process)

    # Start the processes (i.e. calculate the random number lists)      
    for j in jobs:
        j.start()

    # Ensure all of the processes have finished
    for j in jobs:
        j.join()

    print "List processing complete."
"""


def method_friendly_decorator(method_to_decorate):
    def wrapper(self, lie):
        lie = lie - 3 # very friendly, decrease age even more :-)
        return method_to_decorate(self, lie)
    return wrapper


class Lucy(object):

    def __init__(self):
        self.age = 32

    @method_friendly_decorator
    def sayYourAge(self, lie):
        print("I am {0}, what did you think?".format(self.age + lie))

#l = Lucy()
#l.sayYourAge(-3)
#outputs: I am 26, what did you think?

"""
def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper
After this is defined, add the decorator to functions/class methods you want to be threaded like this:

@threaded
def transform(self):
  self.dataframe = (some dataframe computations)
  return self.dataframe
"""