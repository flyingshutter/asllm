from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout import Window
from prompt_toolkit.styles import Style

import tempfile
import os
import atexit

def main():

    # Set up history file in temp dir
    histfile = os.path.join(tempfile.gettempdir(), 'repl_history.txt')

    # Load history if it exists
    command_history = []
    if os.path.exists(histfile):
        with open(histfile, 'r', encoding='utf-8') as f:
            command_history = [line.rstrip('\n') for line in f]
    history_index = [len(command_history)]

    def save_history():
        with open(histfile, 'w', encoding='utf-8') as f:
            for cmd in command_history:
                f.write(cmd + '\n')

    atexit.register(save_history)

    fkeys = [False] * 7  # F1-F7 indicators

    def get_statusbar_text():
        return " | ".join(
            [f"F{i+1}:{'[x]' if fkeys[i] else '[ ]'}" for i in range(7)]
        )

    statusbar = TextArea(
        text=get_statusbar_text(),
        style="class:statusbar",
        height=1,
        focusable=False,
        read_only=True,
    )

    def get_output_height():
        try:
            app = get_app()
            total_height = app.output.get_size().rows
            # 1 for statusbar, 1 for separator, 1 for prompt, 1 for padding
            return max(1, total_height - 4)
        except Exception:
            return 10

    output_area = TextArea(
        style="class:output-area",
        # height=get_output_height,
        focusable=True,
        read_only=True,
        scrollbar=True,
        wrap_lines=False
    )
    
    repl = TextArea(
        prompt='>>> ',
        height=2,
        multiline=True,
        wrap_lines=True,
    )

    root_container = HSplit([
        statusbar,
        # Window(height=1, char=''),
        output_area,
        Window(height=1, char=' '),
        repl,
    ], padding=0)

    style = Style.from_dict({
        'statusbar': 'bg:#4444aa #ffffff',
    })

    kb = KeyBindings()

    @kb.add('c-d')
    def _(event):
        event.app.exit()

    @kb.add('up')
    def _(event):
        if command_history and history_index[0] > 0:
            history_index[0] -= 1
            repl.text = command_history[history_index[0]]

    @kb.add('down')
    def _(event):
        if command_history and history_index[0] < len(command_history) - 1:
            history_index[0] += 1
            repl.text = command_history[history_index[0]]
        else:
            history_index[0] = len(command_history)
            repl.text = ''

    def adjust_repl_height():
        # Set repl height to number of lines in repl.text, min 2, max 10
        lines = repl.text.count('\n') + 1
        repl.height = min(max(lines, 2), 10)

    @kb.add('c-a')
    def _(event):
        # Insert line break at cursor position and adjust height
        buffer = repl.buffer
        buffer.insert_text('\n')
        adjust_repl_height()

    @kb.add('f1')
    def _(event):
        fkeys[0] = not fkeys[0]
        statusbar.text = get_statusbar_text()

    @kb.add('f2')
    def _(event):
        fkeys[1] = not fkeys[1]
        statusbar.text = get_statusbar_text()

    @kb.add('f3')
    def _(event):
        fkeys[2] = not fkeys[2]
        statusbar.text = get_statusbar_text()

    @kb.add('f4')
    def _(event):
        fkeys[3] = not fkeys[3]
        statusbar.text = get_statusbar_text()

    @kb.add('f5')
    def _(event):
        fkeys[4] = not fkeys[4]
        statusbar.text = get_statusbar_text()

    @kb.add('f6')
    def _(event):
        fkeys[5] = not fkeys[5]
        statusbar.text = get_statusbar_text()

    @kb.add('f7')
    def _(event):
        fkeys[6] = not fkeys[6]
        statusbar.text = get_statusbar_text()

    @kb.add('c-y')
    def _(event):
        output_area.text = ''
    
    @kb.add('enter')
    def _(event):
        text = repl.text.strip()
        if text.lower() in ('exit', 'quit'):
            event.app.exit()
        else:
            if text != "":
                command_history.append(text)
                history_index[0] = len(command_history)

                output_area.text += f'You entered: {text}\n'
                output_area.buffer.cursor_position = len(output_area.text)
                repl.text = ''
                adjust_repl_height()
    app = Application(
        layout=Layout(root_container, focused_element=repl),
        key_bindings=kb,
        full_screen=True,
        mouse_support=True,
        style=style,
    )
    app.run()


if __name__ == "__main__":
    main()