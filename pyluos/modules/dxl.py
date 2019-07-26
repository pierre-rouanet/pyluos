from .module import Module, interact

class DynamixelMotor(Module):
    def __init__(self, id, alias, robot):
        Module.__init__(self, 'DynamixelMotor', id, alias, robot)
        # Read
        self.rot_position = None
        self.temperature = None

        # Write
        self._target_rot_position = None
        self._rot_speed = None
        self._compliant = None
        self._wheel_mode = None
        self._power_limit = None
        self._positionPid = [None, None, None]
        self._limit_rot_position = [None, None]

    def _update(self, new_state):
        Module._update(self, new_state)

        if 'rot_position' in new_state:
            self.rot_position = new_state['rot_position']
        if 'temperature' in new_state:
            self.temperature = new_state['temperature']

    @property
    def target_rot_position(self):
        return self._target_rot_position

    @target_rot_position.setter
    def target_rot_position(self, target_position):
        if self._compliant == False:
            self._push_value('target_rot_position', target_position)
            self._target_rot_position = target_position

    @property
    def rot_position_limit(self):
        return self._limit_rot_position

    @rot_position_limit.setter
    def rot_position_limit(self, limit_position):
        self._push_value('limit_rot_position', limit_position)
        self._limit_rot_position = limit_position

    @property
    def target_rot_speed(self):
        return self._rot_speed

    @target_rot_speed.setter
    def target_rot_speed(self, moving_speed):
        self._push_value('target_rot_speed', moving_speed)
        self._rot_speed = moving_speed

    @property
    def positionPid(self):
        return self._positionPid

    @positionPid.setter
    def positionPid(self, new_pid):
        self._positionPid = new_pid
        self._push_value('pid', new_pid)

    # power limit
    @property
    def power_ratio_limit(self):
        if (self._config[ControlledMotor._MODE_POWER] != True):
            print("power mode is not enabled in the module please use 'robot.module.power_mode = True' to enable it")
            return
        return self._power_limit

    @power_ratio_limit.setter
    def power_ratio_limit(self, s):
        s = min(max(s, 0), 100.0)
        self._target_power = s
        self._push_value("power_limit",s)

    @property
    def compliant(self):
        return self._compliant

    @compliant.setter
    def compliant(self, compliant):
        self._push_value('compliant', compliant)
        self._compliant = compliant

    @property
    def wheel_mode(self):
        return self._wheel_mode

    @wheel_mode.setter
    def wheel_mode(self, wheel_mode):
        self._push_value('wheel_mode', wheel_mode)
        self._wheel_mode = wheel_mode

    def set_id(self, id):
        self._push_value('set_id', id)

    def detect(self):
        self._push_value('reinit', 0)

    def register(self, register, val):
        new_val = [register, val]
        self._push_value('register', new_val)

    # notebook things
    def control(self):
        def change_position(target_position):
            self.target_position = target_position

        return interact(change_position, target_position=(-150.0, 150.0, 1.0))
