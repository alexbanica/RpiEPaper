#!/usr/bin/python
# -*- coding:utf-8 -*-

import os
import threading
import time
import logging

from cluster_monitor import RESOURCES_DIR
from cluster_monitor.dto import Context, DiskUsageInfo
from cluster_monitor.renderers import AbstractRenderer, NULL_COORDS, RENDER_ALIGN_LEFT, RENDER_ALIGN_RIGHT, RENDER_ALIGN_CENTER
from waveshare_epd import epd2in7_V2
from PIL import Image, ImageDraw, ImageFont
from cluster_monitor.renderers.ePaper.ePaperController import EPaperController

DEFAULT_SECTION_Y_PADDING = 5
DEFAULT_SECTION_X_PADDING = 5
DEFAULT_FONT_SIZE = 11
DEFAULT_TABLE_FONT_SIZE = 10
COLOR_WHITE=0xff
COLOR_BLACK=0x00
COLOR_GRAY=0x80

def cleanup_epaper():
    epd2in7_V2.epdconfig.module_exit(cleanup=True)

class EPaperRenderer(AbstractRenderer):
    DEFAULT_INIT_INTERVAL = 60*30
    def __init__(self, context: Context, init_interval=DEFAULT_INIT_INTERVAL):
        self.epd = epd2in7_V2.EPD()
        self.fontType = ImageFont.truetype(os.path.join(RESOURCES_DIR, 'Font.ttc'), DEFAULT_FONT_SIZE)
        self.Himage = Image.new('1', (self.epd.height, self.epd.width), COLOR_WHITE)
        self.draw = ImageDraw.Draw(self.Himage)
        self.controller = EPaperController(context)
        self.init_interval = init_interval
        self.hard_refresh()

        self.init_thread = threading.Thread(target=self._run_periodic_init_task, daemon=True)
        self.init_thread.start()

    def hard_refresh(self):
        logging.info("Hard refreshing the rendered content")
        self.epd.init()
        self.epd.Clear()
        self.epd.display_Base_color(COLOR_WHITE)
        self.refresh()

    def _run_periodic_init_task(self):
        while self.init_interval > 0:
            time.sleep(self.init_interval)
            self.hard_refresh()

    def draw_text(self, text: str, prev_coords: tuple[int, int, int, int] = NULL_COORDS,
                  alignment: str = RENDER_ALIGN_LEFT, new_line: bool = True) -> tuple[int, int, int, int]:
        _, _, x2, y2 = prev_coords

        # Calculate text dimensions
        text_width = self.draw.textlength(text, font=self.fontType)
        text_x = DEFAULT_SECTION_X_PADDING
        if not new_line:
            text_x += x2

        if alignment == RENDER_ALIGN_CENTER:
            text_x = (self.epd.height - text_width) // 2
        elif alignment == RENDER_ALIGN_RIGHT:
            text_x = self.epd.height - text_width - DEFAULT_SECTION_X_PADDING

        text_y = y2 + DEFAULT_SECTION_Y_PADDING

        self.draw.text((text_x, text_y), text, font=self.fontType, fill=COLOR_BLACK)

        return text_x, text_y, text_x + text_width, text_y + DEFAULT_FONT_SIZE

    def _clear_specific_area(self, coords: tuple[int, int, int, int]) -> None:
        x1, y1, x2, y2 = coords
        self.draw.rectangle((x1, y1, x2, y2), fill=COLOR_WHITE)

    def draw_new_section(self, prev_coords:tuple[int,int,int,int] = NULL_COORDS) -> tuple[int, int, int, int]:
        _,_,_,y2 = prev_coords
        line_y = y2 + DEFAULT_SECTION_Y_PADDING # Position slightly from the top
        self.draw.line((0, line_y, self.epd.height, line_y), fill=COLOR_BLACK)

        return 0, y2, self.epd.height, line_y

    def draw_new_subsection(self, prev_coords:tuple[int,int, int, int] = NULL_COORDS) -> tuple[int, int, int, int]:
        _,_,_,y2 = prev_coords
        line_y = y2 + DEFAULT_SECTION_Y_PADDING# Position slightly from the top
        line_x =  self.epd.height-2*DEFAULT_SECTION_X_PADDING
        self.draw.line((2*DEFAULT_SECTION_X_PADDING, line_y, line_x, line_y), fill=COLOR_BLACK)

        return (0, self.epd.height, y2, line_y)

    def __close__(self):
        self.controller.__close__()
        logging.info("Closing EpaperRenderer")
        self.init_interval = 0
        self.epd.init()
        self.epd.Clear()
        self.epd.sleep()
        logging.info("EpaperRenderer closed")

    def draw_area(self, x: int, y: int, width: int, height: int, color=None):
        self.draw.rectangle((x, y, x + width, y + height), fill=color or 0)
        print(f"EpaperRenderer: Area drawn at ({x}, {y}, {width}, {height})")  # Optional debug logging

    def refresh(self):
        self._clear_specific_area((0, 0, self.epd.height, self.epd.width))

    def draw_loading(self, prev_coords: tuple[int, int, int, int]):
        _, _, _, y2 = prev_coords
        text_width = self.draw.textlength("Loading...", font=self.fontType)

        center_y = y2 + (self.epd.width - y2) // 2
        center_x = (self.epd.height - text_width) // 2

        self.draw.text(
            (center_x, center_y),
            "Loading...",
            font=self.fontType,
            fill=COLOR_BLACK
        )

    def _draw_apply(self, updated_area):
        newimage = self.Himage.crop(updated_area)
        self.Himage.paste(newimage, updated_area)
        self.epd.display_Partial(self.epd.getbuffer(self.Himage), *updated_area)

    def draw_apply(self):
        self._draw_apply((0, 0, self.epd.width, self.epd.height))

    def draw_paragraph(self, strings: list[str], prev_coords: tuple[int, int, int, int],  current_line: str = "") -> tuple[int, int, int, int]:
        coords = prev_coords

        for string in strings:
            tentative_line = f"{current_line}{string}, "
            text_width = self.draw.textlength(tentative_line, font=self.fontType)

            # Check if the line fits the e-paper width
            if text_width > self.epd.height - 2 * DEFAULT_SECTION_X_PADDING:
                coords = self.draw_text(current_line.rstrip(", "), coords, RENDER_ALIGN_LEFT, False)
                x1, y1, x2, y2 = coords
                coords = (0, y1, 0, y2)
                current_line = f"{string}, "
            else:
                current_line = tentative_line

        # Render any remaining text if present
        if current_line:
            coords = self.draw_text(current_line.rstrip(", "), coords)

        return coords

    @staticmethod
    def shutdown():
        cleanup_epaper()

    def get_controller(self) -> EPaperController:
        return self.controller

    def get_current_page(self) -> int:
        return self.get_controller().get_current_page()

    def get_current_scroll_offset(self) -> int:
        return self.get_controller().get_current_scroll_offset()

    def get_current_scroll_step(self) -> int:
        return self.get_controller().get_current_scroll_step()

    def get_total_pages(self) -> int:
        return self.get_controller().get_total_pages()

    def draw_table(self, headers: dict[str, str], data: list[dict], prev_coords: tuple[int, int, int, int],
                   font_size: int = DEFAULT_TABLE_FONT_SIZE) -> tuple[int, int, int, int]:
        HEADER_BORDER_WIDTH = 2
        INTERNAL_BORDER_WIDTH = 1
        
        _, _, _, start_y = prev_coords
        start_y += DEFAULT_SECTION_Y_PADDING

        # Calculate column widths
        num_columns = len(headers)
        available_width = self.epd.height - (2 * DEFAULT_SECTION_X_PADDING)
        column_width = available_width // num_columns

        # Draw headers
        current_y = start_y

        current_y += HEADER_BORDER_WIDTH
        header_height = font_size + 2 * DEFAULT_SECTION_Y_PADDING
        table_font = ImageFont.truetype(os.path.join(RESOURCES_DIR, 'Font.ttc'), font_size)

        # Draw header cells
        for i, (key, header_text) in enumerate(headers.items()):
            x = DEFAULT_SECTION_X_PADDING + (i * column_width)

            # Draw header text
            text_width = self.draw.textlength(header_text, font=table_font)
            text_x = x + (column_width - text_width) // 2
            text_y = current_y + DEFAULT_SECTION_Y_PADDING
            self.draw.text((text_x, text_y), header_text, font=table_font, fill=COLOR_BLACK)

        current_y += header_height

        # Draw header bottom border
        self.draw.line((DEFAULT_SECTION_X_PADDING, current_y,
                        self.epd.height - DEFAULT_SECTION_X_PADDING, current_y),
                       fill=COLOR_BLACK, width=HEADER_BORDER_WIDTH)

        # Draw data rows
        for row in data:
            row_height = font_size + 2 * DEFAULT_SECTION_Y_PADDING

            # Draw cell contents
            for i, (key, _) in enumerate(headers.items()):
                x = DEFAULT_SECTION_X_PADDING + (i * column_width)

                # Draw cell text
                cell = str(row.get(key, ''))
                text_width = self.draw.textlength(cell, font=table_font)
                text_x = x + (column_width - text_width) // 2
                text_y = current_y + DEFAULT_SECTION_Y_PADDING
                self.draw.text((text_x, text_y), cell, font=table_font, fill=COLOR_BLACK)

            current_y += row_height

            # Draw horizontal border between rows
            self.draw.line((DEFAULT_SECTION_X_PADDING, current_y,
                            self.epd.height - DEFAULT_SECTION_X_PADDING, current_y),
                           fill=COLOR_BLACK, width=INTERNAL_BORDER_WIDTH)

        return (DEFAULT_SECTION_X_PADDING, start_y,
                self.epd.height - DEFAULT_SECTION_X_PADDING, current_y)




