import sys
import os

from AbstractRenderer import AbstractRenderer, NULL_COORDS, RENDER_ALIGN_LEFT, RENDER_ALIGN_RIGHT, RENDER_ALIGN_CENTER
from waveshare_epd import epd2in7_V2
from PIL import Image, ImageDraw, ImageFont
import time

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

DEFAULT_SECTION_Y_PADDING = 5
DEFAULT_SECTION_X_PADDING = 5
DEFAULT_FONT_SIZE = 11
COLOR_WHITE=0xff
COLOR_BLACK=0x00

class EPaperRenderer(AbstractRenderer):
    def __init__(self):
        self.epd = epd2in7_V2.EPD()
        self.fontType = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), DEFAULT_FONT_SIZE)
        self.Himage = Image.new('1', (self.epd.height, self.epd.width), COLOR_WHITE)
        self.draw = ImageDraw.Draw(self.Himage)
        self._init()

    def _init(self):
        self.epd.init()
        self.epd.Clear()
        self.epd.display_Base_color(COLOR_WHITE)
        self.refresh()

    def draw_text(self, text: str, prev_coords: tuple[int, int, int, int] = NULL_COORDS,
                  alignment: str = RENDER_ALIGN_LEFT) -> tuple[int, int, int, int]:
        _, _, x2, y2 = prev_coords

        # Calculate text dimensions
        text_width = self.draw.textlength(text, font=self.fontType)
        text_x = DEFAULT_SECTION_X_PADDING  # Default for ALIGN_LEFT

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
        self.epd.init()
        self.epd.Clear()
        self.epd.sleep()

    def draw_area(self, x: int, y: int, width: int, height: int, color=None):
        """
        Draw a filled rectangle on the e-paper display.
        """
        self.draw.rectangle((x, y, x + width, y + height), fill=color or 0)
        print(f"EpaperRenderer: Area drawn at ({x}, {y}, {width}, {height})")  # Optional debug logging

    def refresh(self):
        self._clear_specific_area((0, 0, self.epd.height, self.epd.width))

    def draw_loading(self, font_size: int = DEFAULT_FONT_SIZE):
        """
            Draws a full-screen loading circle with "Loading..." text in the center of the screen.

            Args:
                font_size (int): Font size for the "Loading..." text. Default is the renderer's font size.
            """
        # Step 1: Initialize font
        loading_font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), font_size)

        # Step 2: Create a blank full-screen canvas
        self.Himage = Image.new('1', (self.epd.height, self.epd.width), COLOR_WHITE)
        self.draw = ImageDraw.Draw(self.Himage)

        # Step 3: Prepare variables for loading animation
        center_x = self.epd.height // 2
        center_y = self.epd.width // 2

        circle_radius = 30  # Radius of the loading circle
        text_y_offset = 40  # Distance from the circle center to the text
        circle_step_angle = 30  # Step for rotating the circle
        angle = 0  # Current rotation angle

        # Step 4: Animation - Rotate the circle
        for _ in range(12):  # Rotate in 12 steps (~360 degrees in total)
            # Clear the screen for the next frame
            self.epd.Clear()

            # Background (white screen)
            self.draw.rectangle((0, 0, self.epd.height, self.epd.width), fill=COLOR_WHITE)

            # Draw the loading circle (only partially)
            for i in range(12):  # Draw the 12 segments of the circle
                start_angle = angle + i * circle_step_angle
                end_angle = start_angle + circle_step_angle - 5  # Gap between segments
                self.draw.arc(
                    [center_x - circle_radius, center_y - circle_radius, center_x + circle_radius,
                     center_y + circle_radius],
                    start=start_angle,
                    end=end_angle,
                    fill=COLOR_BLACK,
                    width=3  # Width of the arc
                )

            # Draw the "Loading..." text
            text_width = self.draw.textlength("Loading...", font=loading_font)
            self.draw.text(
                ((self.epd.height - text_width) // 2, center_y + text_y_offset),
                "Loading...",
                font=loading_font,
                fill=COLOR_BLACK
            )

            # Display the frame on the ePaper
            self.epd.display_Base_color(COLOR_WHITE)
            self.epd.display_Partial(self.epd.getbuffer(self.Himage))

            # Increment angle for next frame (rotation effect)
            angle += circle_step_angle

            # Add delay for animation speed
            time.sleep(0.1)  # ~100ms delay between frames


    def _draw_apply(self, updated_area):
        newimage = self.Himage.crop(updated_area)
        self.Himage.paste(newimage, updated_area)
        self.epd.display_Partial(self.epd.getbuffer(self.Himage), *updated_area)

    def draw_apply(self):
        self._draw_apply((0, 0, self.epd.width, self.epd.height))

    def draw_paragraph(self, strings: list[str], prev_coords: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        current_line = ""
        coords = prev_coords

        for string in strings:
            tentative_line = f"{current_line}{string}, "
            text_width = self.draw.textlength(tentative_line, font=self.fontType)

            # Check if the line fits the e-paper width
            if text_width > self.epd.height - 2 * DEFAULT_SECTION_X_PADDING:
                coords = self.draw_text(current_line.rstrip(", "), coords)
                x1, y1, x2, y2 = coords
                coords = (x1, y1, x2, y2 + DEFAULT_FONT_SIZE)
                current_line = f"{string}, "
            else:
                current_line = tentative_line

        # Render any remaining text if present
        if current_line:
            coords = self.draw_text(current_line.rstrip(", "), coords)

        return coords



