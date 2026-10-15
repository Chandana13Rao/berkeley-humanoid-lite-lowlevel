import sys
import threading
import termios
import tty
import atexit


class Se2Keyboard:
    """Terminal keyboard replacement for Se2Gamepad (works in WSL).

    W/S: forward/back   A/D: turn left/right   Q/E: strafe left/right
    Space: stop         1/2/3: idle/init/RL mode
    """

    def __init__(self, step=0.1, max_vel_x=0.5, max_vel_y=0.5, max_vel_yaw=1.0):
        self.step = step
        self.limits = {"velocity_x": max_vel_x, "velocity_y": max_vel_y, "velocity_yaw": max_vel_yaw}
        self.commands = {"velocity_x": 0.0, "velocity_y": 0.0, "velocity_yaw": 0.0, "mode_switch": 0}
        self._stopped = threading.Event()

    def run(self):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        atexit.register(termios.tcsetattr, fd, termios.TCSADRAIN, old)
        tty.setcbreak(fd)  # single keypresses, Ctrl+C still works
        threading.Thread(target=self._loop, daemon=True).start()
        print("Keyboard: W/S fwd/back, A/D turn, Q/E strafe, Space stop, 1/2/3 mode")

    def stop(self):
        self._stopped.set()

    def _nudge(self, name, direction):
        lim = self.limits[name]
        v = self.commands[name] + direction * self.step
        self.commands[name] = max(-lim, min(lim, round(v, 3)))

    def _loop(self):
        keys = {
            "w": ("velocity_x", +1), "s": ("velocity_x", -1),
            "q": ("velocity_y", +1), "e": ("velocity_y", -1),
            "a": ("velocity_yaw", +1), "d": ("velocity_yaw", -1),
        }
        while not self._stopped.is_set():
            ch = sys.stdin.read(1).lower()
            self.commands["mode_switch"] = 0
            if ch in keys:
                self._nudge(*keys[ch])
            elif ch == " ":
                for k in self.limits:
                    self.commands[k] = 0.0
            elif ch in "123":
                self.commands["mode_switch"] = int(ch)
            c = self.commands
            print(f"\rvx={c['velocity_x']:+.2f}  vy={c['velocity_y']:+.2f}  yaw={c['velocity_yaw']:+.2f}   ",
                  end="", flush=True)


if __name__ == "__main__":
    import time
    kb = Se2Keyboard()
    kb.run()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        kb.stop()