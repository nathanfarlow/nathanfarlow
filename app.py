from io import BytesIO
from flask import Flask, request, redirect, make_response, send_file
from pyboy import PyBoy, WindowEvent

# Made by @arxenix and @nathanfarlow

pyboy = PyBoy('red.gb', window_type='headless', window_scale=3, debug=True, game_wrapper=True)
pyboy.set_emulation_speed(0)

print('starting emulator...', flush=True)
for _ in range(60 * 100):
    pyboy.tick()

app = Flask(__name__)

KEYMAP = {
    'A': (WindowEvent.PRESS_BUTTON_A, WindowEvent.RELEASE_BUTTON_A),
    'B': (WindowEvent.PRESS_BUTTON_B, WindowEvent.RELEASE_BUTTON_B),
    'START': (WindowEvent.PRESS_BUTTON_START, WindowEvent.RELEASE_BUTTON_START),
    'SELECT': (WindowEvent.PRESS_BUTTON_SELECT, WindowEvent.RELEASE_BUTTON_SELECT),
    'UP': (WindowEvent.PRESS_ARROW_UP, WindowEvent.RELEASE_ARROW_UP),
    'DOWN': (WindowEvent.PRESS_ARROW_DOWN, WindowEvent.RELEASE_ARROW_DOWN),
    'LEFT': (WindowEvent.PRESS_ARROW_LEFT, WindowEvent.RELEASE_ARROW_LEFT),
    'RIGHT': (WindowEvent.PRESS_ARROW_RIGHT, WindowEvent.RELEASE_ARROW_RIGHT),
}

frame_skip = 4
seconds_per_input = 5
is_advancing = False

_initial_gif_io = BytesIO()
pyboy.screen_image().save(_initial_gif_io, format='GIF')
current_gif = _initial_gif_io.getvalue()

def advance_game(key):
    global current_gif, is_advancing

    if is_advancing:
        return

    is_advancing = True

    press, release = KEYMAP[key]
    pyboy.send_input(press)

    frames = []

    def next_frame(frame):
        pyboy.tick()
        if frame % frame_skip == 0:
            frames.append(pyboy.screen_image())

    # hold button for 10 frames
    for frame in range(10):
        next_frame(frame)

    # release and wait
    pyboy.send_input(release)
    for frame in range(60 * seconds_per_input - 10):
        next_frame(frame)
    
    # Save frames as gif
    gif_bytes = BytesIO()
    img, *imgs = frames
    img.save(gif_bytes, format='GIF', save_all=True, append_images=imgs,
                duration=1000 * seconds_per_input // len(frames), optimize=True)
    current_gif = gif_bytes.getvalue()

    is_advancing = False

@app.route('/input/<key>')
def do_input(key):
    if key in KEYMAP:
        advance_game(key)
        return redirect('https://github.com/nathanfarlow', code=302)
    else:
        return 'invalid key', 400

@app.route('/game')
def game():
    response = make_response(send_file(BytesIO(current_gif), mimetype='image/gif'))
    response.headers['Cache-Control'] = 'private, max-age=0, no-cache'
    return response

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080)