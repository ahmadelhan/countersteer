# v0.20 NEW FILE - car stereo style mini player for the header
import random
import tkinter as tk

import theme
import animate
import sound

player_width = 250
player_height = 24
frame_ms = 40
eq_every = 3
name_check_every = 12
eq_bars = 5
ticker_left = 40
ticker_right = 192
pause_x = 210
skip_x = 234


class MusicPlayer(tk.Canvas):

    def __init__(self, master):
        super().__init__(master, width = player_width, height = player_height,
                         bg = theme.bg, highlightthickness = 0)
        self.__frame = 0
        self.__afterId = None
        self.__text = None
        self.__textX = ticker_right
        self.__eqHeights = [2] * eq_bars

        self.__draw()
        self.bind("<Destroy>", lambda e: self.__stop())
        self.__tick()

    # drawing
    def __draw(self):
        c = self
        w, h = player_width, player_height
        c.create_rectangle(0, 0, w - 1, h - 1, fill = theme.panel, outline = "")
        self.__text = c.create_text(self.__textX, h // 2, text = "", anchor = "w",
                                    font = theme.fonts["small"], fill = theme.cyan)
        # masks hide the text where it scrolls under the equaliser and buttons
        c.create_rectangle(0, 0, ticker_left - 2, h, fill = theme.panel, outline = "")
        c.create_rectangle(ticker_right, 0, w, h, fill = theme.panel, outline = "")
        c.create_line(ticker_left - 4, 5, ticker_left - 4, h - 5, fill = theme.panel_light)
        c.create_line(ticker_right + 4, 5, ticker_right + 4, h - 5, fill = theme.panel_light)
        self.__drawButtons()
        c.create_rectangle(0, 0, w - 1, h - 1, outline = theme.panel_light)

    def __drawButtons(self):
        c = self
        mid = player_height // 2
        for tag, x, action in [("pauseButton", pause_x, self.__pause),
                               ("skipButton", skip_x, self.__skip)]:
            c.create_rectangle(x - 10, 3, x + 10, player_height - 3, fill = theme.panel,
                               outline = "", tags = (tag, tag + "Back"))
            c.tag_bind(tag, "<Enter>", lambda e, t = tag: self.__hover(t, True))
            c.tag_bind(tag, "<Leave>", lambda e, t = tag: self.__hover(t, False))
            c.tag_bind(tag, "<Button-1>", lambda e, a = action: a())
        # skip: two triangles and a bar
        c.create_polygon(skip_x - 7, mid - 5, skip_x - 1, mid, skip_x - 7, mid + 5,
                         fill = theme.text, tags = ("skipButton", "skipIcon"))
        c.create_polygon(skip_x - 1, mid - 5, skip_x + 5, mid, skip_x - 1, mid + 5,
                         fill = theme.text, tags = ("skipButton", "skipIcon"))
        c.create_rectangle(skip_x + 5, mid - 5, skip_x + 7, mid + 5, fill = theme.text,
                           outline = "", tags = ("skipButton", "skipIcon"))
        self.__drawPauseIcon()

    def __drawPauseIcon(self):
        c = self
        c.delete("pauseIcon")
        mid = player_height // 2
        if sound.isPaused():     # show play
            c.create_polygon(pause_x - 4, mid - 6, pause_x + 6, mid, pause_x - 4, mid + 6,
                             fill = theme.pink, tags = ("pauseButton", "pauseIcon"))
        else:                    # show pause
            for x in (pause_x - 4, pause_x + 2):
                c.create_rectangle(x, mid - 5, x + 3, mid + 5, fill = theme.text,
                                   outline = "", tags = ("pauseButton", "pauseIcon"))

    def __hover(self, tag, over):
        self.itemconfig(tag + "Back", fill = theme.panel_light if over else theme.panel)
        if over:
            sound.playSfx("hover")

    # buttons
    def __pause(self):
        sound.playSfx("click")
        sound.togglePause()
        self.__drawPauseIcon()

    def __skip(self):
        sound.playSfx("click")
        sound.skipTrack()
        self.__checkName(force = True)

    # animation
    def __label(self):
        if sound.isMuted():
            return "MUTED  -  PRESS M"
        name = sound.getTrackName()
        if name == "":
            return "NO TRACK LOADED"
        return f"♪  {name}"

    def __checkName(self, force = False):
        text = self.__label()
        if force or text != self.itemcget(self.__text, "text"):
            self.itemconfig(self.__text, text = text,
                            fill = theme.cyan if sound.isPlaying() else theme.muted)
            self.__textX = ticker_left + 4
            self.coords(self.__text, self.__textX, player_height // 2)
            self.__drawPauseIcon()

    def __scroll(self):
        self.__textX -= 1
        box = self.bbox(self.__text)
        if box is not None and box[2] < ticker_left:    
            self.__textX = ticker_right
        self.coords(self.__text, self.__textX, player_height // 2)

    def __drawEqualiser(self):
        self.delete("eq")
        playing = sound.isPlaying()
        for i in range(eq_bars):
            if playing:
                target = random.randint(3, player_height - 8)
                self.__eqHeights[i] = round((self.__eqHeights[i] + target) / 2)
            else:
                self.__eqHeights[i] = 2
            x = 8 + i * 5
            height = self.__eqHeights[i]
            colour = animate.blend(theme.cyan, theme.pink, i / (eq_bars - 1))
            self.create_rectangle(x, player_height - 5 - height, x + 3, player_height - 5,
                                  fill = colour, outline = "", tags = "eq")

    def __tick(self):
        try:
            if self.__frame % name_check_every == 0:
                self.__checkName()
            if self.__frame % eq_every == 0:
                self.__drawEqualiser()
            self.__scroll()
        except tk.TclError:     
            return
        self.__frame += 1
        self.__afterId = self.after(frame_ms, self.__tick)

    def __stop(self):
        if self.__afterId is not None:
            try:
                self.after_cancel(self.__afterId)
            except tk.TclError:
                pass
            self.__afterId = None