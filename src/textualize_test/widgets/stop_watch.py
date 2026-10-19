from textual.app import ComposeResult
from textual.containers import HorizontalGroup
from textual.widgets import Button

from textualize_test.widgets.time_display import TimeDisplay


class StopWatch(HorizontalGroup):
    """Stop watch widget"""

    def compose(self) -> ComposeResult:
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Reset", id="reset")
        yield TimeDisplay()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        time_display = self.query_one(TimeDisplay)
        if button_id == "start":
            self.add_class("started")
            time_display.start()
        elif button_id == "stop":
            self.remove_class("started")
            time_display.stop()
        elif button_id == "reset":
            self.remove_class("started")
            time_display.reset()
