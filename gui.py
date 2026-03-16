import tkinter as tk
import math, random

# ── Palette ───────────────────────────────────────────────────────────────────
BG        = '#0d1117'
BG_PANEL  = '#161b22'
BG_ITEM   = '#21262d'
BG_HOVER  = '#2d333b'

FG        = '#e6edf3'
FG_SUB    = '#8b949e'
FG_DIM    = '#3d444e'

C_GREEN   = '#3fb950'
C_BLUE    = '#58a6ff'
C_CYAN    = '#4fc3f7'
C_ORANGE  = '#f0883e'
C_RED     = '#ff6b6b'
C_PURPLE  = '#d2a8ff'
C_YELLOW  = '#e3b341'

STATES = {
    'idle':       ('Waiting…',    '#3a3a3a', FG_DIM,   False, 0.08),
    'wake':       ('Listening',   C_GREEN,   C_GREEN,  True,  0.55),
    'recording':  ('Recording',   C_RED,     C_RED,    True,  0.85),
    'processing': ('Processing',  C_ORANGE,  C_ORANGE, True,  0.70),
    'executing':  ('Executing',   C_CYAN,    C_CYAN,   True,  0.75),
    'speaking':   ('Speaking',    C_BLUE,    C_BLUE,   True,  0.90),
    'done':       ('Done',        C_GREEN,   C_GREEN,  False, 0.15),
    'error':      ('Error',       C_RED,     C_RED,    False, 0.15),
}

BAR_COUNT  = 16
BAR_W      = 4
BAR_GAP    = 3
BAR_MAX_H  = 44
BAR_MIN_H  = 3
WAVE_W     = BAR_COUNT * (BAR_W + BAR_GAP) - BAR_GAP


def _lerp_color(a: str, b: str, t: float) -> str:
    ar, ag, ab_ = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    br, bg, bb  = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    return '#{:02x}{:02x}{:02x}'.format(
        int(ar + (br - ar) * t),
        int(ag + (bg - ag) * t),
        int(ab_ + (bb - ab_) * t),
    )


class _Btn(tk.Frame):
    """Flat icon/text button with hover highlight."""
    def __init__(self, parent, text, command, fg=FG_SUB,
                 bg=BG_ITEM, active_fg=FG, hover_bg=BG_HOVER,
                 font=('Segoe UI', 9, 'bold'), padx=14, pady=9, **kw):
        super().__init__(parent, bg=bg, cursor='hand2', **kw)
        self._bg_off = bg
        self._hover  = hover_bg
        self._fg_off = fg
        self._fg_on  = active_fg
        self._cmd    = command
        self._enabled = True

        self._lbl = tk.Label(self, text=text, font=font, bg=bg, fg=fg,
                             padx=padx, pady=pady, cursor='hand2')
        self._lbl.pack()
        for w in (self, self._lbl):
            w.bind('<Enter>',    self._hover_on)
            w.bind('<Leave>',    self._hover_off)
            w.bind('<Button-1>', self._click)

    def _hover_on(self, _=None):
        if self._enabled:
            self.config(bg=self._hover)
            self._lbl.config(bg=self._hover)

    def _hover_off(self, _=None):
        self.config(bg=self._bg_off)
        self._lbl.config(bg=self._bg_off)

    def _click(self, _=None):
        if self._enabled and self._cmd:
            self._cmd()

    def enable(self, yes=True):
        self._enabled = yes
        fg = self._fg_on if yes else FG_DIM
        cur = 'hand2' if yes else 'arrow'
        self._lbl.config(fg=fg, cursor=cur)
        self.config(cursor=cur)

    def set_text(self, t):
        self._lbl.config(text=t)

    def set_fg(self, c):
        self._lbl.config(fg=c)


class FloatingGUI:
    W, H = 320, 510

    def __init__(self, on_quit,
                 on_mic_click=None, on_stop=None,
                 on_back=None, on_refresh=None,
                 on_new_tab=None, on_home=None,
                 on_mute_toggle=None):

        self._callbacks = dict(
            quit=on_quit, mic=on_mic_click, stop=on_stop,
            back=on_back, refresh=on_refresh,
            new_tab=on_new_tab, home=on_home,
            mute=on_mute_toggle,
        )
        self._mic_enabled  = True
        self._stop_enabled = False
        self._muted        = False
        self._current_state = 'idle'
        self._tick         = 0
        self._bar_phases   = [random.uniform(0, 2 * math.pi) for _ in range(BAR_COUNT)]
        self._bar_speeds   = [random.uniform(0.06, 0.14) for _ in range(BAR_COUNT)]
        self._bar_heights  = [BAR_MIN_H] * BAR_COUNT

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.96)
        self.root.configure(bg=BG)

        sw = self.root.winfo_screenwidth()
        self.root.geometry(f'{self.W}x{self.H}+{sw - self.W - 16}+20')

        self._build()
        self._animate()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # Header ───────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG_PANEL, height=44)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)

        tk.Label(hdr, text='◈', font=('Segoe UI', 13),
                 bg=BG_PANEL, fg=C_BLUE).pack(side='left', padx=(14, 4), pady=10)
        tk.Label(hdr, text='FRIDAY', font=('Segoe UI', 11, 'bold'),
                 bg=BG_PANEL, fg=FG).pack(side='left')

        close = tk.Label(hdr, text='✕', font=('Segoe UI', 9),
                         bg=BG_PANEL, fg=FG_DIM, cursor='hand2')
        close.pack(side='right', padx=12)
        close.bind('<Button-1>', lambda e: self._callbacks['quit']())
        close.bind('<Enter>', lambda e: close.config(fg=C_RED))
        close.bind('<Leave>', lambda e: close.config(fg=FG_DIM))

        self._mute_lbl = tk.Label(hdr, text='🔊', font=('Segoe UI', 11),
                                   bg=BG_PANEL, fg=FG_DIM, cursor='hand2')
        self._mute_lbl.pack(side='right', padx=(0, 4))
        self._mute_lbl.bind('<Button-1>', self._toggle_mute)
        self._mute_lbl.bind('<Enter>', lambda e: self._mute_lbl.config(fg=FG_SUB))
        self._mute_lbl.bind('<Leave>', lambda e: self._mute_lbl.config(
            fg=C_RED if self._muted else FG_DIM))

        for w in (hdr,):
            w.bind('<ButtonPress-1>', self._drag_start)
            w.bind('<B1-Motion>',     self._drag_move)

        tk.Frame(self.root, bg=BG_ITEM, height=1).pack(fill='x')

        # Waveform + status ────────────────────────────────────────
        status_outer = tk.Frame(self.root, bg=BG, height=130)
        status_outer.pack(fill='x')
        status_outer.pack_propagate(False)

        # Waveform canvas (centred)
        self._wave_canvas = tk.Canvas(
            status_outer, width=WAVE_W, height=BAR_MAX_H + 4,
            bg=BG, highlightthickness=0
        )
        self._wave_canvas.pack(pady=(14, 6))
        self._bars = []
        for i in range(BAR_COUNT):
            x = i * (BAR_W + BAR_GAP)
            bid = self._wave_canvas.create_rectangle(
                x, BAR_MAX_H, x + BAR_W, BAR_MAX_H,
                fill=FG_DIM, outline='', tags='bar'
            )
            self._bars.append(bid)

        # Status row
        st_row = tk.Frame(status_outer, bg=BG)
        st_row.pack(fill='x', padx=16)

        self._state_var = tk.StringVar(value='Waiting…')
        self._state_lbl = tk.Label(st_row, textvariable=self._state_var,
                                    font=('Segoe UI', 14, 'bold'),
                                    bg=BG, fg=FG_DIM, anchor='w')
        self._state_lbl.pack(fill='x')

        self._sub_var = tk.StringVar(value='Say "Hey Friday" or press Speak')
        self._sub_lbl = tk.Label(st_row, textvariable=self._sub_var,
                                  font=('Segoe UI', 8),
                                  bg=BG, fg=FG_DIM, anchor='w', wraplength=280)
        self._sub_lbl.pack(fill='x')

        tk.Frame(self.root, bg=BG_ITEM, height=1).pack(fill='x', padx=14)

        # ── Bottom sections packed FIRST so log can expand into middle ──

        # Main controls (bottom)
        ctrl = tk.Frame(self.root, bg=BG_PANEL, height=72)
        ctrl.pack(side='bottom', fill='x')
        ctrl.pack_propagate(False)

        inner = tk.Frame(ctrl, bg=BG_PANEL)
        inner.place(relx=0.5, rely=0.5, anchor='center')

        self._mic_btn = _Btn(inner, '🎤  Speak', self._mic_click,
                              fg=FG_SUB, active_fg=FG,
                              font=('Segoe UI', 9, 'bold'), padx=20, pady=10)
        self._mic_btn.pack(side='left', padx=(0, 8))

        self._stop_btn = _Btn(inner, '⏹  Stop', self._stop_click,
                               fg=FG_DIM, hover_bg='#2a1515',
                               font=('Segoe UI', 9, 'bold'), padx=20, pady=10)
        self._stop_btn.pack(side='left')

        tk.Frame(self.root, bg=BG_ITEM, height=1).pack(side='bottom', fill='x')

        # Browser controls (bottom, above main controls)
        browser_row = tk.Frame(self.root, bg=BG_PANEL, height=42)
        browser_row.pack(side='bottom', fill='x')
        browser_row.pack_propagate(False)

        tk.Label(browser_row, text='BROWSER', font=('Segoe UI', 7, 'bold'),
                 bg=BG_PANEL, fg=FG_DIM).pack(side='left', padx=(14, 8))

        browser_btns = tk.Frame(browser_row, bg=BG_PANEL)
        browser_btns.pack(side='right', padx=10)

        nav_font = ('Segoe UI', 10)
        self._back_btn    = self._nav_btn(browser_btns, '←', self._cb('back'),    nav_font)
        self._refresh_btn = self._nav_btn(browser_btns, '⟳', self._cb('refresh'), nav_font)
        self._newtab_btn  = self._nav_btn(browser_btns, '+', self._cb('new_tab'), nav_font)
        self._home_btn    = self._nav_btn(browser_btns, '⌂', self._cb('home'),    nav_font)

        tk.Frame(self.root, bg=BG_ITEM, height=1).pack(side='bottom', fill='x')

        # Activity log (fills remaining middle space) ──────────────
        log_outer = tk.Frame(self.root, bg=BG)
        log_outer.pack(side='top', fill='both', expand=True, padx=14, pady=(8, 4))

        log_hdr = tk.Frame(log_outer, bg=BG)
        log_hdr.pack(fill='x', pady=(0, 5))
        tk.Label(log_hdr, text='ACTIVITY', font=('Segoe UI', 7, 'bold'),
                 bg=BG, fg=FG_DIM).pack(side='left')
        clr = tk.Label(log_hdr, text='clear', font=('Segoe UI', 7),
                        bg=BG, fg=FG_DIM, cursor='hand2')
        clr.pack(side='right')
        clr.bind('<Button-1>', lambda e: self._clear_log())
        clr.bind('<Enter>',    lambda e: clr.config(fg=FG_SUB))
        clr.bind('<Leave>',    lambda e: clr.config(fg=FG_DIM))

        log_wrap = tk.Frame(log_outer, bg=BG_PANEL)
        log_wrap.pack(fill='both', expand=True)

        self._log = tk.Text(
            log_wrap, bg=BG_PANEL, fg=FG_SUB,
            font=('Consolas', 8), relief='flat',
            state='disabled', cursor='arrow',
            wrap='word', padx=8, pady=6,
            insertbackground=BG_PANEL,
            selectbackground=BG_ITEM,
            spacing1=2, spacing3=2,
        )
        self._log.pack(side='left', fill='both', expand=True)

        sb = tk.Scrollbar(log_wrap, command=self._log.yview,
                          bg=BG_PANEL, troughcolor=BG_PANEL,
                          highlightthickness=0, bd=0, width=5)
        sb.pack(side='right', fill='y')
        self._log.config(yscrollcommand=sb.set)

        for tag, color in (('ok', C_GREEN), ('active', C_CYAN), ('warn', C_YELLOW),
                            ('error', C_RED), ('dim', FG_DIM), ('command', C_PURPLE),
                            ('speaking', C_BLUE)):
            self._log.tag_config(tag, foreground=color)
        self._log.tag_config('command', font=('Consolas', 8, 'bold'))

    def _nav_btn(self, parent, text, cmd, font):
        lbl = tk.Label(parent, text=text, font=font,
                        bg=BG_PANEL, fg=FG_DIM, cursor='hand2',
                        padx=9, pady=6)
        lbl.pack(side='left')
        lbl.bind('<Button-1>', lambda e: cmd() if lbl.cget('fg') != FG_DIM else None)
        lbl.bind('<Enter>',    lambda e: lbl.config(fg=FG if lbl.cget('fg') != FG_DIM else FG_DIM))
        lbl.bind('<Leave>',    lambda e: lbl.config(fg=FG_SUB if lbl._enabled else FG_DIM)
                                         if hasattr(lbl, '_enabled') else None)
        lbl._enabled = False
        return lbl

    def _set_nav_enabled(self, enabled: bool):
        color = FG_SUB if enabled else FG_DIM
        cur   = 'hand2' if enabled else 'arrow'
        for btn in (self._back_btn, self._refresh_btn,
                    self._newtab_btn, self._home_btn):
            btn.config(fg=color, cursor=cur)
            btn._enabled = enabled

    # ── Animation ─────────────────────────────────────────────────────────────

    def _animate(self):
        self._tick += 1
        _, dot_color, _, pulsing, amplitude = STATES.get(
            self._current_state, ('', FG_DIM, '', False, 0.08))

        for i, bid in enumerate(self._bars):
            self._bar_phases[i] += self._bar_speeds[i] * (2.5 if pulsing else 0.4)
            raw = (math.sin(self._bar_phases[i]) + 1) / 2   # 0..1
            # add a second harmonic for irregularity
            raw2 = (math.sin(self._bar_phases[i] * 1.7 + 1.3) + 1) / 4
            val = (raw * 0.75 + raw2 * 0.25) * amplitude
            h = max(BAR_MIN_H, int(val * BAR_MAX_H))
            top = BAR_MAX_H - h
            x = i * (BAR_W + BAR_GAP)
            self._wave_canvas.coords(bid, x, top, x + BAR_W, BAR_MAX_H)

            # colour: lerp from dim to active colour based on height
            t = h / BAR_MAX_H
            color = _lerp_color('#1e2630', dot_color, t)
            self._wave_canvas.itemconfig(bid, fill=color)

        self.root.after(45, self._animate)

    # ── Drag ──────────────────────────────────────────────────────────────────

    def _drag_start(self, e):
        self._dx, self._dy = e.x, e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f'+{x}+{y}')

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _cb(self, name):
        return lambda: self._callbacks[name]() if self._callbacks.get(name) else None

    def _mic_click(self):
        if self._mic_enabled and self._callbacks.get('mic'):
            self._callbacks['mic']()

    def _stop_click(self):
        if self._stop_enabled and self._callbacks.get('stop'):
            self._callbacks['stop']()

    def _toggle_mute(self, _=None):
        self._muted = not self._muted
        self._mute_lbl.config(text='🔇' if self._muted else '🔊',
                               fg=C_RED if self._muted else FG_DIM)
        if self._callbacks.get('mute'):
            self._callbacks['mute'](self._muted)

    # ── Log ───────────────────────────────────────────────────────────────────

    def add_log(self, text: str, level: str = 'dim'):
        prefix = {'ok': '✓ ', 'active': '⟳ ', 'error': '✗ ',
                   'warn': '! ', 'command': '▶ ', 'speaking': '🔊 ',
                   'dim': '  '}.get(level, '  ')
        def _do():
            self._log.config(state='normal')
            self._log.insert('end', prefix + text + '\n', level)
            self._log.see('end')
            self._log.config(state='disabled')
        self.root.after(0, _do)

    def _clear_log(self):
        self._log.config(state='normal')
        self._log.delete('1.0', 'end')
        self._log.config(state='disabled')

    # ── State ─────────────────────────────────────────────────────────────────

    def set_state(self, state: str, subtitle: str = ''):
        label, _, text_color, _, _ = STATES.get(state, ('?', FG_DIM, FG_SUB, False, 0.1))
        self._current_state = state

        mic_active  = state in ('idle', 'done')
        stop_active = state in ('wake', 'recording', 'processing', 'executing', 'speaking')
        nav_active  = state in ('idle', 'done')

        self.root.after(0, self._apply, label, text_color, subtitle,
                         mic_active, stop_active, nav_active)

    def _apply(self, label, color, subtitle, mic_on, stop_on, nav_on):
        self._state_var.set(label)
        self._state_lbl.config(fg=color)
        short = (subtitle[:44] + '…') if len(subtitle) > 44 else subtitle
        self._sub_var.set(short)
        self._sub_lbl.config(fg=FG_SUB if subtitle else FG_DIM)

        self._mic_enabled  = mic_on
        self._stop_enabled = stop_on
        self._mic_btn.enable(mic_on)
        self._stop_btn.enable(stop_on)
        self._stop_btn.set_fg(C_RED if stop_on else FG_DIM)
        self._set_nav_enabled(nav_on)

    def start(self):
        self.root.mainloop()
