from gpiozero import Button
import logging
import threading
import time

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
        logging.info("Closing ePaper key thread")
        self.running = False
        self.thread.join()
        logging.info("Thread %s: finished", self.thread.name)

    def _check_epaper_key_pressed_task(self):
        while self.running:
            def __key1_pressed():
                logging.info("Key 1 pressed - switching to page 1")
                setattr(self, 'current_page', 1)

            def __key2_pressed():
                logging.info("Key 2 pressed - switching to page 2")
                setattr(self, 'current_page', 2)

            def __key3_pressed():
                logging.info("Key 3 pressed - switching to page 3")
                setattr(self, 'current_page', 3)

            self.key1.when_pressed = __key1_pressed
            self.key2.when_pressed = __key2_pressed
            self.key3.when_pressed = __key3_pressed
            # self.key4.when_pressed = lambda: setattr(self, 'current_page', 4)
            time.sleep(0.5)

    def get_current_page(self):
        return self.current_page

    def get_total_pages(self):
        return 4
