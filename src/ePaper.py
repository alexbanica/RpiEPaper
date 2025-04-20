from gpiozero import Button
import logging
import threading


class ePaper:
    def __init__(self):

        self.key2 = Button(6)
        self.key3 = Button(13)
        self.key1 = Button(5)
        # self.key4 = Button(17)

        self.running = True
        self.current_page = 1
        self.thread = threading.Thread(target=self._check_epaper_key_pressed_task, daemon=True)
        self.thread.start()
        logging.info("ePaper update thread [%s] started.", self.thread.name)
    
    def __close__(self):
        self.running = False
        self.thread.join()
        logging.info("Thread %s: finishing", self.thread.name)

    def _check_epaper_key_pressed_task(self):
        while self.running:
            self.key1.when_pressed = lambda: setattr(self, 'current_page', 1)
            self.key2.when_pressed = lambda: setattr(self, 'current_page', 2)
            self.key3.when_pressed = lambda: setattr(self, 'current_page', 3)
            # self.key4.when_pressed = lambda: setattr(self, 'current_page', 4)

    def get_current_page(self):
        return self.current_page

    def get_total_pages(self):
        return 4
