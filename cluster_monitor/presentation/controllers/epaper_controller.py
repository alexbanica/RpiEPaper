import logging
import threading
import time

from gpiozero import Button

from cluster_monitor.domain.entities import ContextEntity


class EpaperController:
    def __init__(self, context: ContextEntity):
        buttons = []
        try:
            self.key1 = Button(5)
            buttons.append(self.key1)
            self.key2 = Button(6)
            buttons.append(self.key2)
            self.key3 = Button(13)
            buttons.append(self.key3)
            self.key4 = Button(19)
            buttons.append(self.key4)

            self.running = True
            self._close_condition = threading.Condition()
            self._closed = False
            self._close_owner = None
            self._close_error = None
            self.current_page = context.default_page
            self.scroll_offset = 0
            self.scroll_step = 5

            self.thread = threading.Thread(target=self._check_epaper_key_pressed_task, daemon=True)
            self.thread.start()
        except BaseException:
            for button in buttons:
                try:
                    button.close()
                except Exception:
                    logging.exception("Failed to close partially initialized ePaper button")
            raise
        logging.info("ePaper update thread [%s] started.", self.thread.name)

    def close(self) -> None:
        current = threading.get_ident()
        with self._close_condition:
            if self._closed:
                if self._close_error is not None:
                    raise self._close_error
                return
            if self._close_owner is not None:
                if self._close_owner == current:
                    return
                while not self._closed:
                    self._close_condition.wait()
                if self._close_error is not None:
                    raise self._close_error
                return
            self._close_owner = current
            self.running = False
        failures = []
        if self.thread is not threading.current_thread():
            try:
                self.thread.join()
            except Exception as error:
                failures.append(error)
                logging.exception("Failed to join ePaper button thread")
        for button in (self.key1, self.key2, self.key3, self.key4):
            try:
                button.close()
            except Exception as error:
                failures.append(error)
                logging.exception("Failed to close ePaper button")
        with self._close_condition:
            self._close_error = failures[0] if failures else None
            self._closed = True
            self._close_owner = None
            self._close_condition.notify_all()
        logging.info("Thread %s: finished", self.thread.name)
        if failures:
            raise failures[0]

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
