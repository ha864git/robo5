from machine import Timer
import micropython
import servo_sg90_kitronik5348_robo5
import robo5_angles_ini
import robo5_motions
import machine


class robo5:

    def __init__(self):
        self._servomotor = servo_sg90_kitronik5348_robo5.PIOServo()
        self._angles = [90, 90, 90, 90, 90]
        self._angles_ini = [
            robo5_angles_ini.hr_ini,
            robo5_angles_ini.kr_ini,
            robo5_angles_ini.hl_ini,
            robo5_angles_ini.kl_ini,
            robo5_angles_ini.ws_ini,
        ]
        self._list_pointer = 0
        self._done = 1
        self._cmd_request = "stop"
        self._cmd_continue = ""
        self._cmd_terminate = ""
        self._next_command = ""
        self._update_angle()
        self._playing_list = []
        self._playing_mode = "stop"
        self._repeat = 0
        self.motions = robo5_motions.motions
        self._motions_str = ""
        self._intervalTimer = Timer()
        micropython.alloc_emergency_exception_buf(100)
        self._intervalTimer.init(mode=Timer.PERIODIC, freq=50, callback=self._timeover)

    def get_angles(self):
        hr = self._angles[0]
        kr = self._angles[1]
        hl = self._angles[2]
        kl = self._angles[3]
        ws = self._angles[4]
        return hr, kr, hl, kl, ws

    def get_angles_ini(self):
        hr_ini = self._angles_ini[0]
        kr_ini = self._angles_ini[1]
        hl_ini = self._angles_ini[2]
        kl_ini = self._angles_ini[3]
        ws_ini = self._angles_ini[4]
        return hr_ini, kr_ini, hl_ini, kl_ini, ws_ini

    def set_angles_ini(self, hr_ini, kr_ini, hl_ini, kl_ini, ws_ini):
        self._angles_ini = [hr_ini, kr_ini, hl_ini, kl_ini, ws_ini]
        fstr = "hr_ini = " + str(hr_ini)
        fstr += "\n" + "kr_ini = " + str(kr_ini)
        fstr += "\n" + "hl_ini = " + str(hl_ini)
        fstr += "\n" + "kl_ini = " + str(kl_ini)
        fstr += "\n" + "ws_ini = " + str(ws_ini)
        f = open("robo5_angles_ini.py", "w")
        f.write(fstr)
        f.close()

    def get_motion(self, motion_num):
        if motion_num < 0 or motion_num >= len(self.motions):
            return "", ""
        return self.motions[motion_num][0], self.motions[motion_num][1]

    def set_motions(self, str):
        fstr = str.replace("\\n", "\n")
        f = open("robo5_motions.py", "w")
        f.write(fstr)
        f.close()
        print("Please restart the program to apply the new motions.")

    def set_angle_direct(self, hr, kr, hl, kl, ws):
        list = ["direct", "", "", [[[hr, 1], [kr, 1], [hl, 1], [kl, 1], [ws, 1]]]]
        found = False
        for i in range(len(self.motions)):
            if self.motions[i][0] == list[0]:
                self.motions[i] = list
                found = True
                break
        if not found:
            self.motions.append(list)
        self.set_request_name(list[0])

    def set_request_name(self, name):
        for mo in self.motions:
            if mo[0] == name:
                self._cmd_request = name
                return True
        return False

    def _update_angle(self):
        for i in range(5):
            self._servomotor.goToPosition(i, self._angles[i] + self._angles_ini[i] - 90)

    def _timeover(self, timer):
        if self._done == 0:
            self._execute_command()
        if self._done == 1:
            self._check_command()

    def _execute_command(self):
        if len(self._playing_list) > 0:
            if 0 == self._set_angle(
                self._playing_list[self._list_pointer]
            ):  # Angle reached
                self._list_pointer += 1  # Next step
            if self._list_pointer >= len(self._playing_list):  # End of motion list
                self._list_pointer = 0  # Reset pointer
                self._done = 1  # Mark done
                if self._cmd_continue == "":
                    if self._playing_mode == self._cmd_request:
                        self._cmd_request = self._playing_mode + "_done"
                        self._playing_mode = self._cmd_request
                else:
                    if self._playing_mode != self._cmd_request:
                        self._cmd_request = self._cmd_terminate
                    else:
                        self._cmd_request = self._cmd_continue
                    self._playing_mode = self._playing_mode + "_done"

    def _check_command(self):
        if self._playing_mode != self._cmd_request:  # New command
            print(self._playing_mode, self._cmd_request)
            for mo in self.motions:
                if mo[0] == self._cmd_request:
                    self._playing_list = []
                    for p in mo[3]:
                        l = []
                        l.append(90 + p[0][0])  # HR
                        l.append(90 + p[1][0])  # KR
                        l.append(90 - p[2][0])  # HL
                        l.append(90 - p[3][0])  # KL
                        l.append(90 + p[4][0])  # WS
                        l.append(p[0][1])  # pitch HR
                        l.append(p[1][1])  # pitch KR
                        l.append(p[2][1])  # pitch HL
                        l.append(p[3][1])  # pitch KL
                        l.append(p[4][1])  # pitch WS
                        self._playing_list.append(l)
                    self._playing_mode = self._cmd_request
                    self._cmd_continue = mo[1]
                    self._cmd_terminate = mo[2]
                    self._list_pointer = 0
                    self._done = 0
                    break

    def _set_angle(self, list):
        ans_set_angle = 0
        for i in range(5):
            self._angles[i] = self._get_angle(self._angles[i], list[i], list[i + 5])
            if self._angles[i] != list[i]:
                ans_set_angle += 1
            self._servomotor.goToPosition(i, self._angles[i] + self._angles_ini[i] - 90)
        return ans_set_angle

    def _get_angle(self, current, target, pitch):
        ans_get_angle = current
        if pitch == 0:
            ans_get_angle = target
        elif ans_get_angle >= target + pitch:
            ans_get_angle -= pitch
        elif ans_get_angle <= target - pitch:
            ans_get_angle += pitch
        else:
            ans_get_angle = target
        return ans_get_angle
