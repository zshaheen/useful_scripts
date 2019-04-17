import threading
import multiprocessing
import ctypes


class OddEvenMonitor(object):
    ODD_TURN = 'odd'
    EVEN_TURN = 'even'

    def __init__(self):
        super(OddEvenMonitor, self).__init__()
        self.turn = multiprocessing.Value(ctypes.c_char_p, self.ODD_TURN)
        self.cv = multiprocessing.Condition()
    
    def wait_turn(self, old_turn):
        with self.cv:
            print('self.turn.value', self.turn.value)
            print('old_turn', old_turn)
            while self.turn.value != old_turn:
                print('{} is waiting, cause self.turn is {}'.format(old_turn, self.turn.value))
                self.cv.wait()

    def toggle_turn(self):
        with self.cv:
            if self.turn.value == self.ODD_TURN:
                # self.turn = multiprocessing.Value(ctypes.c_char_p, self.EVEN_TURN)
                self.turn.value = self.EVEN_TURN
            else:
                # self.turn = multiprocessing.Value(ctypes.c_char_p, self.ODD_TURN)
                self.turn.value = self.ODD_TURN
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
