"""
Testing the synchronus printing of stuff, like how
`zstash extract` with multiprocessing would work.
"""
import sys
import multiprocessing
import collections
import ctypes


class NotYourTurnError(BaseException):
    """
    An error to let a worker know it needs to wait
    to print it's stuff.
    """
    pass

class PrintMonitor(object):
    """
    Used to synchronize the printing of the output between workers.
    Depending on the current_tar, the worker processing the work
    for that tar will print it's output.
    """        
    def __init__(self, tars_to_print, *args, **kwargs):
        # A list of tars to print.
        # Ex: ['000000.tar', '000008.tar', '00001a.tar']
        if not tars_to_print:
            msg = "You must pass in a list of tars, which dictates"
            msg += " the order of which to print the results."
            raise RuntimeError(msg)
        
        # The variables below are modified/accessed by different processes,
        # so they need to be in shared memory.
        self._cv = multiprocessing.Condition()

        self._tars_to_print = multiprocessing.Queue()
        for tar in tars_to_print:
            self._tars_to_print.put(tar)

        # We need a manager to instantiate the Value instead of multiprocessing.Value.
        # If we didn't use a manager, it seems to get some junk value.
        self._manager = multiprocessing.Manager()
        self._current_tar = self._manager.Value(ctypes.c_char_p, self._tars_to_print.get())

    def wait_turn(self, worker, workers_curr_tar, *args, **kwargs):
        """
        While a worker's current tar isn't the one
        needed to be printed, wait.

        A process can pass in a timeout, and if the turn
        isn't given within that, a NotYourTurnError is raised.
        """
        with self._cv:
            while self._current_tar.value != workers_curr_tar:
                try:
                    self._cv.wait(*args, **kwargs)
                except RuntimeError:
                    raise NotYourTurnError()

    def done_dequeuing_output_for_tar(self, worker, workers_curr_tar, *args, **kwargs):
        """
        A worker has finished printing the output for workers_curr_tar
        from the print queue.
        If possible, update self._current_tar.
        If there aren't anymore tars to print, set self._current_tar to None.
        """
        # It must be the worker's turn before this can happen.
        self.wait_turn(worker, workers_curr_tar, *args, **kwargs)

        with self._cv:
            self._current_tar.value = self._tars_to_print.get() if not self._tars_to_print.empty() else ''
            self._cv.notify_all()


class ExtractWorker(object):
    """
    An object that is attached to a Process.
    It redirects all of the output of the logging module to a queue.
    Then with a PrintMonitor, it prints to the
    terminal in the order defined by the PrintMonitor.
    
    This worker is called during `zstash extract`.
    """
    class PrintQueue(collections.deque):
        """
        A queue with a write() function.
        This is so that this can be replaced with sys.stdout in the extractFiles function.
        This way, all calls to `print()` will be sent here.
        """
        def __init__(self):
            self.TarAndMsg = collections.namedtuple('TarAndMsg', ['tar', 'msg'])
            self.curr_tar = None

        def write(self, msg):
            if self.curr_tar:
                self.append(self.TarAndMsg(self.curr_tar, msg))

        def flush(self):
            # Not needed, but it's called by some interal Python code.
            # So we need to provide a function like this.
            pass

    def __init__(self, print_monitor, tars_to_work_on, failure_queue, *args, **kwargs):
        """
        print_monitor is used to determine if it's this worker's turn to print.
        tars_to_work_on is a list of the tars that this worker will process.
        """
        self.print_monitor = print_monitor
        # Every call to print() in the original function will
        # be piped to this queue instead of the screen.
        self.print_queue = self.PrintQueue()
        # A tar is mapped to True when all of its output is in the queue.
        self.is_output_done_enqueuing = {tar:False for tar in tars_to_work_on}
        # After extractFiles is done, all of the failures will be added to this queue.
        self.failure_queue = failure_queue

    def set_curr_tar(self, tar):
        """
        Sets the current tar this worker is working on.
        """
        self.print_queue.curr_tar = tar
    
    def done_enqueuing_output_for_tar(self, tar):
        """
        All of the output for extracting this tar is in the print queue.
        """
        if not tar in self.is_output_done_enqueuing:
            msg = 'This tar {} isn\'t assigned to this worker.'
            raise RuntimeError(msg.format(tar))

        if self.is_output_done_enqueuing[tar]:
            msg = 'This tar ({}) was already told to be done.'
            raise RuntimeError(msg.format(tar))

        self.is_output_done_enqueuing[tar] = True
    
    def print_contents(self):
        """
        Try to print the contents from self.print_queue.
        """
        try:
            # Wait for 0.001 seconds to see if it's our turn.
            self.print_all_contents(0.001)
        except NotYourTurnError:
            # It's not our turn, so try again the next time this function is called.
            pass
    
    def has_to_print(self):
        """
        Returns True if this Worker still has things to print.
        """
        return len(self.print_queue) >= 1

    def print_all_contents(self, *args, **kwargs):
        """
        Block until all of the contents of self.print_queue are printed.

        If it's not our turn and the passed in timeout to print_monitor.wait_turn
        is over, a NotYourTurnError exception is raised.
        """
        while self.has_to_print():
            # print(self.name, 'HAS to print something...')
            # Try to print the first element in the queue.
            tar_to_print = self.print_queue[0].tar
            # print(tar_to_print)
            self.print_monitor.wait_turn(self, tar_to_print, *args, **kwargs)
            # print('It is ', self.name, 'turn now')

            # Print all applicable values in the print_queue.
            while self.print_queue and self.print_queue[0].tar == tar_to_print:
                msg = self.print_queue.popleft().msg
                print(msg)

            # If True, then all of the output for extracting tar_to_print was in the queue.
            # Since we just finished printing all of it, we can move onto the next one.
            if self.is_output_done_enqueuing[tar_to_print]:
                # Let all of the other workers know that this worker is done.
                # print(self.name, 'is letting the others know it is done.')
                self.print_monitor.done_dequeuing_output_for_tar(self, tar_to_print)

import logging
import time
logging.basicConfig(filename='something.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

def print_tars(tars_to_print, multiprocess_worker=None):
    """
    Print some info about these tars using the logging module.
    """
    if multiprocess_worker:
        sh = logging.StreamHandler(multiprocess_worker.print_queue)
        sh.setLevel(logging.DEBUG)
        logger.addHandler(sh)
        
    for tar in tars_to_print:
        if multiprocess_worker:
            multiprocess_worker.set_curr_tar(tar)

        # We print the info for each tar twice.
        for i in range(2):
            logger.info('try {}: {} tar is doing work'.format(i, tar))
            logger.info('try {}: {} tar is doing work 1'.format(i, tar))
            logger.info('try {}: {} tar is doing work 2'.format(i, tar))
            logger.info('try {}: {} tar is doing work 3'.format(i, tar))

            if i == 1:
                multiprocess_worker.done_enqueuing_output_for_tar(tar)
                # print('{} work is done being enqueued.'.format(tar))

            if multiprocess_worker:
                multiprocess_worker.print_contents()
            # time.sleep(1)

    if multiprocess_worker:
        # If there are stuff left to print, print them.
        # print('trying to print ALL (ALL!!) contents of', multiprocess_worker)
        multiprocess_worker.print_all_contents()
        # Add the failures to the queue.
        '''
        for f in failures:
            multiprocess_worker.failure_queue.add(f)
        '''
        # print('DONE PRINTING THE CONTENTS OF', multiprocess_worker)




tars = ['00.tar', '03.tar', '04.tar', '07.tar', '10.tar', '12.tar', '15.tar']
# We're testing with three workers.
workers_to_tar = [['00.tar', '07.tar','15.tar'], ['03.tar', '12.tar'], ['04.tar','10.tar']]
monitor = PrintMonitor(tars)

# The return value for extractFiles will be added here.
failures = multiprocessing.Queue()
processes = []
for i, tars_for_this_worker in enumerate(workers_to_tar):
    worker = ExtractWorker(monitor, tars_for_this_worker, failures)
    process = multiprocessing.Process(target=print_tars, args=(tars_for_this_worker, worker))
    process.start()
    processes.append(process)

for p in processes:
    p.join()
