from abc import ABC, abstractmethod

RENDER_ALIGN_CENTER = "center"
RENDER_ALIGN_LEFT = "left"
RENDER_ALIGN_RIGHT = "right"
NULL_COORDS = (0, 0, 0, 0)

class AbstractRenderer(ABC):
    @abstractmethod
    def draw_text(self, text:str, prev_coords:tuple[int,int, int, int] = NULL_COORDS, alignment:str=RENDER_ALIGN_LEFT) -> tuple[int, int, int, int]:
        pass

    @abstractmethod
    def draw_new_section(self, prev_coords:tuple[int,int, int, int] = NULL_COORDS) -> tuple[int, int, int, int]:
        pass

    @abstractmethod
    def draw_new_subsection(self, prev_coords:tuple[int,int, int, int] = NULL_COORDS) -> tuple[int, int, int, int]:
        pass

    @abstractmethod
    def refresh(self) -> None:
        pass

    @abstractmethod
    def draw_loading(self):
        pass

    def __close__(self):
        pass


    @abstractmethod
    def draw_area(self, x: int, y: int, width: int, height: int, color=None):
        pass

    @abstractmethod
    def draw_apply(self):
        pass

    @abstractmethod
    def draw_paragraph(self, strings: list[str], prev_coords: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        pass

