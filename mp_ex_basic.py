import threading
import multiprocessing
import ctypes


class OddEvenMonitor(object):
    ODD_TURN = 'odd'
    EVEN_TURN = 'even'

    def __init__(self):
        super(OddEvenMonitor, self).__init__()
        arr = ['odd' if i%2 == 1 else 'even' for i in range(1, 102)]
        # self.orders = multiprocessing.Array(ctypes.c_char_p, arr)
        self.orders = multiprocessing.Queue()
        for turn in arr:
            self.orders.put(turn)

        self.manager = multiprocessing.Manager()
        # self.turn = multiprocessing.Value(ctypes.c_char_p, self._get_next_tar()) 
        self.turn = self.manager.Value(ctypes.c_char_p, self.orders.get()) 
        self.cv = multiprocessing.Condition()

    def wait_turn(self, old_turn):
        with self.cv:
            print('self.turn.value', self.turn.value)
            print('old_turn', old_turn)
            while self.turn.value != old_turn:
                print('{} is waiting, cause self.turn is {}'.format(old_turn, self.turn.value))
                print('self.turn.value', self.turn.value)
                self.cv.wait()

    def toggle_turn(self):
        with self.cv:
            # self.turn.value = self._get_next_tar()
            new_turn = self.orders.get() if not self.orders.empty() else ''
            print('new_turn', new_turn)
            self.turn.value = new_turn  # ctypes.c_char_p(new_turn).value
            print('It is now the turn of', self.turn.value)
            self.cv.notify_all()

class OddProcess(multiprocessing.Process):
    def __init__(self, monitor):
        super(OddProcess, self).__init__()
        self.monitor = monitor
    
    def run(self):
        for i in range(1, 101, 2):
            print('Odd is doing something')
            self.monitor.wait_turn(OddEvenMonitor.ODD_TURN)
            print(i)
            self.monitor.toggle_turn()

class EvenProcess(multiprocessing.Process):
    def __init__(self, monitor):
        super(EvenProcess, self).__init__()
        self.monitor = monitor
    
    def run(self):
        for i in range(2, 101, 2):
            print('Even is doing something')
            self.monitor.wait_turn(OddEvenMonitor.EVEN_TURN)
            print(i)
            self.monitor.toggle_turn()

monitor = OddEvenMonitor()
p1 = EvenProcess(monitor)
p2 = OddProcess(monitor)

p1.start()
p2.start()

p1.join()
p2.join()
