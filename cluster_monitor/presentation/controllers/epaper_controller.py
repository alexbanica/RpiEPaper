import logging
import threading
import time

from gpiozero import Button

from cluster_monitor.domain.entities import ContextEntity


class EpaperController:
    def __init__(self, context: ContextEntity):
        self.key1 = Button(5)
        self.key2 = Button(6)
        self.key3 = Button(13)
        self.key4 = Button(19)

        self.running = True
        self.current_page = context.default_page
        self.scroll_offset = 0
        self.scroll_step = 5

        self.thread = threading.Thread(target=self._check_epaper_key_pressed_task, daemon=True)
        self.thread.start()
        logging.info("ePaper update thread [%s] started.", self.thread.name)

    def close(self) -> None:
        self.running = False
        self.thread.join()
        logging.info("Thread %s: finished", self.thread.name)

    def _check_epaper_key_pressed_task(self) -> None:
        while self.running:
            self.key1.when_pressed = self._key1_pressed
            self.key2.when_pressed = self._key2_pressed
            self.key3.when_pressed = self._key3_pressed
            self.key4.when_pressed = self._key4_pressed
            time.sleep(0.2)

    def _key1_pressed(self) -> None:
        self.scroll_offset = 0
        self.current_page = 1

    def _key2_pressed(self) -> None:
        self.scroll_offset = 0
        self.current_page = 2

    def _key3_pressed(self) -> None:
        if self.current_page == 2:
            self.scroll_offset = max(0, self.scroll_offset - self.scroll_step)
            return

        self.current_page = 3
        self.scroll_offset = 0

    def _key4_pressed(self) -> None:
        if self.current_page == 2:
            self.scroll_offset = min(1000, self.scroll_offset + self.scroll_step)
            return

        self.current_page = 4
        self.scroll_offset = 0

    def get_current_page(self) -> int:
        return self.current_page

    def get_current_scroll_step(self) -> int:
        return self.scroll_step

    def get_current_scroll_offset(self) -> int:
        return self.scroll_offset

    def get_total_pages(self) -> int:
        return 4
