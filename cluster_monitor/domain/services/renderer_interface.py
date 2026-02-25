from abc import ABC, abstractmethod

from cluster_monitor.shared.constants import NULL_COORDS, RENDER_ALIGN_LEFT


class RendererInterface(ABC):
    @abstractmethod
    def draw_text(
        self,
        text: str,
        prev_coords: tuple[int, int, int, int] = NULL_COORDS,
        alignment: str = RENDER_ALIGN_LEFT,
        new_line: bool = True,
    ) -> tuple[int, int, int, int]:
        raise NotImplementedError

    @abstractmethod
    def draw_new_section(self, prev_coords: tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int, int, int]:
        raise NotImplementedError

    @abstractmethod
    def draw_new_subsection(self, prev_coords: tuple[int, int, int, int] = NULL_COORDS) -> tuple[int, int, int, int]:
        raise NotImplementedError

    @abstractmethod
    def refresh(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def hard_refresh(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw_loading(self, prev_coords: tuple[int, int, int, int]) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw_apply(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw_paragraph(
        self,
        strings: list[str],
        prev_coords: tuple[int, int, int, int],
        current_line: str = "",
    ) -> tuple[int, int, int, int]:
        raise NotImplementedError

    @abstractmethod
    def get_controller(self) -> object:
        raise NotImplementedError

    @abstractmethod
    def get_current_page(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_current_scroll_offset(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_current_scroll_step(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_total_pages(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def draw_table(
        self,
        headers: dict[str, str],
        data: list[dict],
        prev_coords: tuple[int, int, int, int],
    ) -> tuple[int, int, int, int]:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    def draw_pagination(self) -> str:
        return f" - p{self.get_current_page()}/{self.get_total_pages()}"
