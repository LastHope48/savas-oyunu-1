import threading
import time


class Result:
    def __init__(self):
        self.value = None
        self.done = False

    def get(self):
        while not self.done:
            time.sleep(0.01)
        return self.value


def after(func, *args, secs: int):
    r'''
    Programı durdurmadan bir süre geçtikten sonra bir fonksiyonu çalıştırır (tek sefer).
    '''
    def wrapper():
        time.sleep(secs)
        func(*args)
    t = threading.Thread(target=wrapper, daemon=True)
    t.start()
    return t


def after_return(func, *args, secs: float, result: Result):
    r'''
    Programı durdurmadan bir süre geçtikten sonra verilen fonksiyonun verdiği değeri döndürür.
    '''

    def wrapper():
        time.sleep(secs)
        result.value = func(*args)
        result.done = True

    t = threading.Thread(target=wrapper, daemon=True)
    t.start()
    return result


def every(func, *args, secs: int, loops=-1):
    r'''
    Programı durdurmadan belirlenen süre sonra bir fonksiyonu çalıştırır (döngü).
    '''
    def wrapper():
        nonlocal loops
        while loops != 0:  # Loops negatif olursa sonsuza kadar tekrarlanacağı göze alınmıştır.
            time.sleep(secs)
            func(*args)
            loops -= 1
    t = threading.Thread(target=wrapper)
    t.start()
    return t

