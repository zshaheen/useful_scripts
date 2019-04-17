import threading
import multiprocessing

class OddEvenMonitor(threading._Condition):
    ODD_TURN = True
    EVEN_TURN = False

    def __init__(self):
        super(OddEvenMonitor, self).__init__()
        self.turn = self.ODD_TURN
    
    def wait_turn(self, old_turn):
        with self:
            while self.turn != old_turn:
                self.wait()

    def toggle_turn(self):
        with self:
            self.turn ^= True
            self.notify()

class OddThread(threading.Thread):
    def __init__(self, monitor):
        super(OddThread, self).__init__()
        self.monitor = monitor
    
    def run(self):
        for i in range(1, 101, 2):
            self.monitor.wait_turn(OddEvenMonitor.ODD_TURN)
            print(i)
            self.monitor.toggle_turn()

class EvenThread(threading.Thread):
    def __init__(self, monitor):
        super(EvenThread, self).__init__()
        self.monitor = monitor
    
    def run(self):
        for i in range(2, 101, 2):
            self.monitor.wait_turn(OddEvenMonitor.EVEN_TURN)
            print(i)
            self.monitor.toggle_turn()

monitor = OddEvenMonitor()
t1 = EvenThread(monitor)
t2 = OddThread(monitor)

t1.start()
t2.start()

t1.join()
t2.join()
