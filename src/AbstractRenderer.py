from abc import ABC, abstractmethod

RENDER_ALIGN_CENTER = "center"
RENDER_ALIGN_LEFT = "left"
RENDER_ALIGN_RIGHT = "right"
NULL_COORDS = (0, 0, 0, 0)

class AbstractRenderer(ABC):
    @abstractmethod
    def draw_text(self, text:str, prev_coords:tuple[int,int, int, int] = NULL_COORDS, alignment:str = RENDER_ALIGN_LEFT, new_line:bool = True) -> tuple[int, int, int, int]:
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
    def hard_refresh(self) -> None:
        pass

    @abstractmethod
    def draw_loading(self):
        pass

    @abstractmethod
    def draw_area(self, x: int, y: int, width: int, height: int, color=None):
        pass

    @abstractmethod
    def draw_apply(self):
        pass

    @abstractmethod
    def draw_paragraph(self, strings: list[str], prev_coords: tuple[int, int, int, int], current_line: str = "") -> tuple[int, int, int, int]:
        pass

    @abstractmethod
    def get_controller(self):
        pass

    @abstractmethod
    def get_current_page(self) -> int:
        pass

    @abstractmethod
    def get_total_pages(self) -> int:
        pass

    def draw_pagination(self):
        return " - p"+str(self.get_current_page()) + "/" + str(self.get_total_pages())

    @abstractmethod
    def draw_table(self, headers:dict[str, str], data:list[dict], prev_coords: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        pass

