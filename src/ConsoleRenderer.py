from AbstractRenderer import AbstractRenderer
import logging

from AbstractRenderer import NULL_COORDS, RENDER_ALIGN_LEFT, RENDER_ALIGN_RIGHT, RENDER_ALIGN_CENTER


class ConsoleRenderer(AbstractRenderer):

    def __init__(self):
        """
        Initializes the ConsoleRenderer.
        Sets up logging for console output.
        """
        self.logger = logging.getLogger("ConsoleRenderer")
        logging.basicConfig(level=logging.INFO)  # Configure logging level
        self.section_delimiter = '=' * 50  # Delimiter for new sections
        self.subsection_delimiter = '-' * 50  # Delimiter for new subsections
        self.line_width = 50  # Assumed line width for alignment purposes

    def draw_text(self, text: str, prev_coords: tuple[int, int, int, int] = NULL_COORDS,
                  alignment: str = RENDER_ALIGN_LEFT) -> tuple[int, int, int, int]:
        """
        Logs text with the specified alignment.

        Args:
            text (str): The text to 'draw'.
            prev_coords (tuple[int, int, int, int]): The previous coordinates.
            alignment (str): Alignment of the text (left, center, right).

        Returns:
            tuple[int, int, int, int]: Simulated new coordinates after "drawing" the text.
        """
        line = ""
        if alignment == RENDER_ALIGN_LEFT:
            line = text.ljust(self.line_width)
        elif alignment == RENDER_ALIGN_RIGHT:
            line = text.rjust(self.line_width)
        elif alignment == RENDER_ALIGN_CENTER:
            line = text.center(self.line_width)

        self.logger.info(line)

        # Simulated coordinates: shifting down by 1 unit (just for logging mimicry)
        _, _, x2, y2 = prev_coords
        return (0, y2, len(text), y2 + 1)

    def draw_new_section(self, prev_coords: tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int, int, int]:
        """
        Logs a new section delimiter.

        Args:
            prev_coords (tuple[int, int, int, int]): Previous coordinates.

        Returns:
            tuple[int, int, int, int]: Updated coordinates to simulate section spacing.
        """
        self.logger.info(self.section_delimiter)
        _, _, _, y2 = prev_coords
        return (0, y2, self.line_width, y2 + 1)

    def draw_new_subsection(self, prev_coords: tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int, int, int]:
        """
        Logs a new subsection delimiter.

        Args:
            prev_coords (tuple[int, int, int, int]): Previous coordinates.

        Returns:
            tuple[int, int, int, int]: Updated coordinates to simulate subsection spacing.
        """
        self.logger.info(self.subsection_delimiter)
        _, _, _, y2 = prev_coords
        return (0, y2, self.line_width, y2 + 1)

    def draw_area(self, x: int, y: int, width: int, height: int, color=None):
        """
        Logs a rectangle or an area being drawn.

        Args:
            x (int): The x-coordinate of the top-left corner.
            y (int): The y-coordinate of the top-left corner.
            width (int): The width of the rectangle.
            height (int): The height of the rectangle.
            color (optional): The color of the rectangle.
        """
        self.logger.info(f"Drawing area at ({x}, {y}) with width={width}, height={height}, color={color}")

    def refresh(self) -> None:
        """
        Logs a refresh operation.
        """
        self.logger.info("Refreshing the rendered content")

    def draw_loading(self):
        """
        Logs a loading message.
        """
        self.logger.info("Loading...")

    def draw_apply(self):
        pass

    def __close__(self):
        """
        Clears the logs (mocks closing the renderer).
        """
        self.logger.info("Closing ConsoleRenderer")

    def draw_paragraph(self, strings: list[str], prev_coords: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        paragraph = ", ".join(strings)
        start_index = 0
        _, _, _, y2 = prev_coords

        while start_index < len(paragraph):
            line = paragraph[start_index:start_index + self.line_width]
            # Adjust to not cut words between lines
            if len(line) == self.line_width and start_index + self.line_width < len(paragraph):
                last_space = line.rfind(" ")
                if last_space != -1:
                    line = line[:last_space]
            self.logger.info(line)
            start_index += len(line.lstrip())
            y2 += 1  # Increment vertical coordinates to simulate new line

        return 0, prev_coords[1], self.line_width, y2

