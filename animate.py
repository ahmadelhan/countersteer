import tkinter as tk

import theme
import sound

frame_ms = 16
hover_ms = 140          # how long hover fades
pulse_ms = 220          # how long the click fades
count_ms = 450          # how long number takes to count new value
fade_ms = 140           # screen transition

_running = {}           # (widget, what) -> after id, so a new animation replaces an old one
_transitionBusy = False


# colours
def hexToRgb(colour):
    colour = colour.lstrip("#")
    return tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4))


def rgbToHex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in rgb)


def blend(start, end, amount):
    a, b = hexToRgb(start), hexToRgb(end)
    return rgbToHex([a[i] + (b[i] - a[i]) * amount for i in range(3)])


def lighter(colour, amount = 0.22):
    return blend(colour, "#ffffff", amount)


def ease(t):
    return 1 - (1 - t) ** 3


# running an animation 
def _cancel(widget, what):
    key = (str(widget), what)
    if key in _running:
        try:
            widget.after_cancel(_running.pop(key))
        except tk.TclError:
            pass


def animate(widget, what, duration, step, done = None):
    _cancel(widget, what)
    frames = max(1, duration // frame_ms)

    def tick(frame):
        try:
            step(ease(frame / frames))
        except tk.TclError:             # widget destroyed mid-animation
            _running.pop((str(widget), what), None)
            return
        if frame < frames:
            _running[(str(widget), what)] = widget.after(frame_ms, lambda: tick(frame + 1))
        else:
            _running.pop((str(widget), what), None)
            if done is not None:
                done()

    tick(0)


def fadeColour(widget, option, start, end, duration = hover_ms):
    animate(widget, option, duration, lambda t: widget.config(**{option: blend(start, end, t)}))


# buttons
def styleButton(button, colour):
    hover = lighter(colour)
    button.config(activebackground = hover)
    state = {"over": False}

    def enter(event):
        state["over"] = True
        if str(button.cget("state")) != "disabled":
            sound.playSfx("hover")
        fadeColour(button, "bg", button.cget("bg"), hover)

    def leave(event):
        state["over"] = False
        fadeColour(button, "bg", button.cget("bg"), colour)

    def press(event):
        sound.playSfx("click")
        target = hover if state["over"] else colour
        fadeColour(button, "bg", "#ffffff", target, pulse_ms)

    button.bind("<Enter>", enter, add = "+")
    button.bind("<Leave>", leave, add = "+")
    button.bind("<ButtonPress-1>", press, add = "+")
    return button


# numbers 
def countTo(label, old, new, fmt = "{:,}"):
    if old == new:
        label.config(text = fmt.format(new))
        return
    animate(label, "count", count_ms,
            lambda t: label.config(text = fmt.format(round(old + (new - old) * t))))


# screen transition
def _setAlpha(root, value):
    try:
        root.attributes("-alpha", value)
    except tk.TclError:               
        pass


def fadeIn(root):
    _setAlpha(root, 0.0)
    animate(root, "alpha", fade_ms, lambda t: _setAlpha(root, t))


def transition(root, build):
    global _transitionBusy
    if _transitionBusy:
        return
    _transitionBusy = True

    def swap():
        global _transitionBusy
        try:
            build()
        finally:
            _transitionBusy = False
        animate(root, "alpha", fade_ms, lambda t: _setAlpha(root, t))

    animate(root, "alpha", fade_ms, lambda t: _setAlpha(root, 1 - t), swap)


def stopAll():
    for (name, what), afterId in list(_running.items()):
        try:
            tk._default_root.after_cancel(afterId)
        except (tk.TclError, AttributeError):
            pass
    _running.clear()