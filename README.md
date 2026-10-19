# Textualize Test

A small Textual TUI app: three independent stopwatches in a scrollable list.
Used as a learning project for how Textual wires widgets, styles, messages,
reactive state, and timers together.

Run with `uv run tui` from the project root.

## Project layout

```
pyproject.toml                      # entry point: tui -> textualize_test:main
src/textualize_test/
  __init__.py                       # main(): MainWindow().run()
  mainwindow/
    mainwindow.py                   # App subclass, builds the screen
    mainwindow.tcss                 # styles for everything
  widgets/
    stop_watch.py                   # StopWatch: buttons + display
    time_display.py                 # TimeDisplay: the ticking clock
```

## Textual concepts used here

- **App**: root object. Owns the terminal, the event loop, CSS, and key bindings. `.run()` starts it.
- **Widget**: anything on screen. Widgets form a DOM tree, like a web page.
- **Containers**: `HorizontalGroup`, `VerticalScroll`, etc. Arrange child widgets.
- **`compose()`**: declares the child tree. Yielded widgets are mounted automatically.
- **TCSS**: CSS-like stylesheet. Selectors are type (`Button`), id (`#start`), or class (`.started`).
- **Reactive attributes**: `reactive(...)` class attributes. Assigning a new value triggers watchers and a refresh.
- **Messages**: widgets post messages (e.g. `Button.Pressed`). They bubble up the DOM unless stopped.
- **Bindings / actions**: keys map to action names, which dispatch to `action_<name>` methods.
- **Timers**: `set_interval(...)` returns a timer that can be `pause()`d and `resume()`d.

## Startup flow

1. The `tui` script calls `textualize_test:main()`, which runs `MainWindow().run()`.
2. `MainWindow` (an `App`) loads `mainwindow.tcss` through `CSS_PATH`. The path is resolved relative to the module.
3. `compose()` yields `Header`, `Footer`, and a `VerticalScroll` holding three `StopWatch` widgets.
4. `BINDINGS` maps `D` to `action_toggle_dark`. The method is inherited from `App`, so this file does not define it.

## StopWatch flow

`StopWatch` is a `HorizontalGroup` containing a Start button, a Stop button, a Reset button, and a `TimeDisplay`.

### Button press to handler

1. The user clicks a button. Button's `_on_click` calls `press()`, which posts `Button.Pressed(self)`.
2. The message bubbles from the button up its parents: `StopWatch`, then `VerticalScroll`, then the app.
3. Textual looks for a handler by name. The name comes from the message class: `Button.Pressed` becomes `on_button_pressed`. Textual walks the class MRO and calls every matching method it finds.
4. `StopWatch.on_button_pressed` runs. It checks `event.button.id` and does one of three things:
   - **start**: `add_class("started")`, then `time_display.start()`
   - **stop**: `remove_class("started")`, then `time_display.stop()`
   - **reset**: `remove_class("started")`, then `time_display.reset()`

The handler never changes colors, visibility, or layout. Adding or removing the `started` class is the only state change it makes. The CSS does the rest:

```tcss
.started #start  { display: none }    /* hide Start while running */
.started #stop   { display: block }   /* show Stop while running */
.started #reset  { visibility: hidden }
```

This is the main pattern in the project: **Python changes state through classes, and CSS decides how that state looks.**

### Reactive attributes to watchers

`TimeDisplay` declares three reactive attributes:

```python
start_time = reactive(monotonic)   # callable default: evaluated for the initial value
time = reactive(0.0)
total = reactive(0.0)
```

When code assigns `self.time = x`, Textual's descriptor does the following:

1. Runs any `validate_time` method, if one exists.
2. Compares the new value with the current one. If they are equal, nothing else happens.
3. If the value changed, calls `watch_time(old, new)` if it exists (the number of parameters decides what is passed), then schedules a refresh.

So `watch_time` is never called by hand. It runs as a side effect of `self.time = ...`. Here it formats the value and updates the `Digits` display:

```python
def watch_time(self, time: float) -> None:
    minutes, seconds = divmod(time, 60)
    hours, minutes = divmod(minutes, 60)
    self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")
```

### Timers to the clock

`on_mount` creates a 60 fps interval, paused at first:

```python
self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)
```

- Each tick calls `update_time`, which sets `self.time = total + (monotonic() - start_time)`. That assignment triggers `watch_time`, which redraws the display.
- `start()` records `start_time = monotonic()` and resumes the timer.
- `stop()` pauses the timer and adds the elapsed segment to `total`. Totals survive across start/stop cycles, so the time does not drift.
- `reset()` sets `total` and `time` back to zero.

Using `monotonic()` for elapsed time means the display stays correct even if the tick rate varies.

### Why the methods run without being called

Nothing in the project calls `on_button_pressed`, `watch_time`, `update_time`, or `action_toggle_dark` directly. Textual calls them through name-based dispatch:

| You write | Textual calls it when |
|---|---|
| `on_button_pressed(self, event)` | a `Button.Pressed` message reaches this widget |
| `on_mount(self)` | the widget is mounted |
| `watch_time(self, value)` | `self.time` is assigned a different value |
| `action_toggle_dark(self)` | a bound key (`D`) runs the action |
| `update_time` (passed to `set_interval`) | the timer fires |

Each widget has its own message queue, processed by its own task. Handlers on one widget run one at a time.

## Notes

- Three `StopWatch` instances reuse the ids `#start`, `#stop`, and `#reset`. This works because `query_one` is scoped to each `StopWatch`, and the CSS is meant to style all three the same way. It would be a problem if code outside a `StopWatch` needed to target one specific button.
- `TimeDisplay.on_mount` creates the timer. Calling `start()` before mount would fail.
- `# self.time = monotonic() - self.start_time` in `time_display.py` is a leftover commented-out line.
- The Reset button is hidden with `visibility`, not `display`, so it still takes up space while the stopwatch runs.
- Requires Python 3.14 and `textual>=8.2.8`.
