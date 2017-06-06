import sys
import time
import threading

from queue import Queue
from datetime import datetime
from collections import defaultdict

from .io import io_from_host
from .modules import name2mod
from .metrics import Publisher


def run_from_unittest():
    return 'unittest' in sys.modules


class Robot(object):
    _heartbeat_timeout = 10  # in sec.

    def __init__(self, host, *args, **kwargs):
        self._io = io_from_host(host=host,
                                *args, **kwargs)

        # We force a first poll to setup our model.
        self._setup(self._poll_once())
        self._last_update = time.time()
        self._running = True

        # Setup both poll/push synchronization loops.
        self._poll_bg = threading.Thread(target=self._poll_and_up)
        self._poll_bg.daemon = True
        self._poll_bg.start()
        self._push_bg = threading.Thread(target=self._push_update)
        self._push_bg.daemon = True
        self._push_bg.start()

        if not run_from_unittest():
            self._metrics_pub = Publisher(robot=self)
            self._metrics_pub.start()

    @property
    def state(self):
        return {
            'gate': self.name,
            'timestamp': datetime.now(),
            'types': ','.join([mod.type for mod in self.modules]),
            'modules': ','.join([mod.alias for mod in self.modules])
        }

    @property
    def name(self):
        return self._name

    @property
    def alive(self):
        dt = time.time() - self._last_update
        return dt < self._heartbeat_timeout

    def close(self):
        self._running = False
        self._poll_bg.join()

    def _setup(self, state):
        gate = next(g for g in state['modules']
                    if g['type'] == 'gate')
        self._name = gate['alias']

        modules = [mod for mod in state['modules']
                   if mod['type'] in name2mod.keys()]

        self._msg_stack = Queue()

        self.modules = [
            name2mod[mod['type']](id=mod['id'],
                                  alias=mod['alias'],
                                  robot=self)
            for mod in modules
        ]
        # We push our current state to make sure that
        # both our model and the hardware are synced.
        self._push_once()

        for mod in self.modules:
            setattr(self, mod.alias, mod)

    # Poll state from hardware.
    def _poll_once(self):
        return self._io.read()

    def _poll_and_up(self):
        while self._running:
            self._update(self._poll_once())

    # Update our model with the new state.
    def _update(self, new_state):
        mod_need_update = [mod for mod in new_state['modules']
                           if hasattr(self, mod['alias']) and
                           set(mod.keys()) != {'type', 'id', 'alias'}]

        for mod in mod_need_update:
            getattr(self, mod['alias'])._update(mod)

        self._last_update = time.time()

    # Push update from our model to the hardware
    def _push_once(self):
        data = defaultdict(dict)
        while not self._msg_stack.empty():
            msg = self._msg_stack.get()

            key, val = msg.popitem()
            data[key].update(val)

        if data:
            self._send({
                'modules': data
            })

    def _push_update(self):
        while self._running:
            msg = self._msg_stack.get()

            # TODO: instead of pushing each time
            # we have a message on the stack
            # We could use a buffer.
            self._send({
                'modules': msg
            })

    def _send(self, msg):
        self._io.send(msg)