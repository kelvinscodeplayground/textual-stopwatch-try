from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header

from textualize_test.widgets.stop_watch import StopWatch


class MainWindow(App):
    """A simple Textual app to demonstrate the main window."""

    CSS_PATH = "mainwindow.tcss"
    BINDINGS: ClassVar[list[BindingType]] = [("D", "toggle_dark", "Toggle dark mode")]
    TITLE = "Textualize Test"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield VerticalScroll(StopWatch(), StopWatch(), StopWatch())
