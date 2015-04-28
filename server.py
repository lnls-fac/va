
import time
import threading
import va.model as model


def run(model):
    model.process()


class ModelThread(threading.Thread):

    pass


if __name__ == '__main__':
    si = model.SiModel()

    t = ModelThread(target=run, args=(si,))
    t.start()

    time.sleep(2)

    si._queue.put('STOP')

    print(si._accelerator.energy)
