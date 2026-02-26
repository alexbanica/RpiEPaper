import logging
import time

from cluster_monitor.domain.entities import ContextEntity
from cluster_monitor.presentation.renderers.abstract_renderer import (
    AbstractRenderer,
    NULL_COORDS,
    RENDER_ALIGN_CENTER,
    RENDER_ALIGN_LEFT,
    RENDER_ALIGN_RIGHT,
)


class ConsoleRenderer(AbstractRenderer):
    def __init__(self, context: ContextEntity):
        self.logger = logging.getLogger("ConsoleRenderer")
        self.section_delimiter = "=" * 50
        self.subsection_delimiter = "-" * 50
        self.line_width = 50
        self.context = context

    def draw_text(
        self,
        text: str,
        prev_coords: tuple[int, int, int, int] = NULL_COORDS,
        alignment: str = RENDER_ALIGN_LEFT,
        new_line: bool = True,
    ) -> tuple[int, int, int, int]:
        if alignment == RENDER_ALIGN_RIGHT:
            line = text.rjust(self.line_width)
        elif alignment == RENDER_ALIGN_CENTER:
            line = text.center(self.line_width)
        else:
            line = text.ljust(self.line_width)

        self.logger.info(line)
        _, _, _, y2 = prev_coords
        return 0, y2, len(text), y2 + 1

    def draw_new_section(self, prev_coords: tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int, int, int]:
        self.logger.info(self.section_delimiter)
        _, _, _, y2 = prev_coords
        return 0, y2, self.line_width, y2 + 1

    def draw_new_subsection(self, prev_coords: tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int, int, int]:
        self.logger.info(self.subsection_delimiter)
        _, _, _, y2 = prev_coords
        return 0, y2, self.line_width, y2 + 1

    def refresh(self) -> None:
        self.logger.info("Refreshing rendered content")

    def hard_refresh(self) -> None:
        self.logger.info("Hard refreshing rendered content")

    def draw_loading(self, prev_coords: tuple[int, int, int, int]) -> None:
        self.logger.info("Loading...")
        time.sleep(5)

    def draw_apply(self) -> None:
        return None

    def draw_paragraph(
        self,
        strings: list[str],
        prev_coords: tuple[int, int, int, int],
        current_line: str = "",
    ) -> tuple[int, int, int, int]:
        paragraph = current_line + ", ".join(strings)
        start_index = 0
        _, _, _, y2 = prev_coords

        while start_index < len(paragraph):
            line = paragraph[start_index : start_index + self.line_width]
            if len(line) == self.line_width and start_index + self.line_width < len(paragraph):
                last_space = line.rfind(" ")
                if last_space != -1:
                    line = line[:last_space]
            self.logger.info(line)
            start_index += len(line.lstrip())
            y2 += 1

        return 0, prev_coords[1], self.line_width, y2

    def get_controller(self):
        return self

    def get_current_page(self) -> int:
        return self.context.default_page

    def get_total_pages(self) -> int:
        return 4

    def get_current_scroll_step(self) -> int:
        return 100

    def get_current_scroll_offset(self) -> int:
        return 0

    def draw_table(
        self,
        headers: dict[str, str],
        data: list[dict],
        prev_coords: tuple[int, int, int, int],
    ) -> tuple[int, int, int, int]:
        header_keys = list(headers.keys())
        col_widths = [len(headers[key]) for key in header_keys]
        for row in data:
            for index, key in enumerate(header_keys):
                if key in row:
                    col_widths[index] = max(col_widths[index], len(str(row[key])))

        padding = 2
        total_width = sum(col_widths) + (padding * (len(headers) - 1))

        header_line = ""
        for index, key in enumerate(header_keys):
            header_line += headers[key].ljust(col_widths[index])
            if index < len(header_keys) - 1:
                header_line += " " * padding

        coords = self.draw_text(header_line, prev_coords)
        coords = self.draw_text("-" * total_width, coords)

        for row in data:
            row_line = ""
            for index, key in enumerate(header_keys):
                row_line += str(row.get(key, "")).ljust(col_widths[index])
                if index < len(header_keys) - 1:
                    row_line += " " * padding
            coords = self.draw_text(row_line, coords)

        return coords

    def close(self) -> None:
        self.logger.info("Closing ConsoleRenderer")
