import bluetooth
from ble_simple_peripheral import BLESimplePeripheral
import machine
import robo5


def main():
    ble = bluetooth.BLE()   # Create BLE object
    ble.active(True)        # Activate BLE
    p = BLESimplePeripheral(ble)       # Create BLE peripheral

    led = machine.Pin("LED", machine.Pin.OUT)   # Initialize on-board LED
    robo = robo5.robo5()    # Create robo5 object

    def on_rx(data):    # Callback for received data
        cmd = data.decode("utf-8").replace("\n", "")
        print('cmd:' + cmd)
        if not robo.set_request_name(cmd):
            if cmd == "get angles_init":
                hr, kr, hl, kl, ws = robo.get_angles_ini()
                tx_str = (
                    "ri "
                    + str(hr)
                    + ","
                    + str(kr)
                    + ","
                    + str(hl)
                    + ","
                    + str(kl)
                    + ","
                    + str(ws)
                )
                print(tx_str)
                p.send(tx_str)
                return
            elif cmd == "get angles":
                hr, kr, hl, kl, ws = robo.get_angles()
                tx_str = (
                    "ra "
                    + str(hr)
                    + ","
                    + str(kr)
                    + ","
                    + str(hl)
                    + ","
                    + str(kl)
                    + ","
                    + str(ws)
                )
                print(tx_str)
                p.send(tx_str)
                return
            else:
                para = cmd.split(" ")
                if len(para) == 2:
                    angles = para[1].split(",")
                    if para[0] == "si":
                        robo.set_angles_ini(
                            int(angles[0]),
                            int(angles[1]),
                            int(angles[2]),
                            int(angles[3]),
                            int(angles[4]),
                        )
                        robo.set_angle_direct(0, 0, 0, 0, 0)
                        return
                    if para[0] == "sa":
                        robo.set_angle_direct(
                            int(angles[0]),
                            int(angles[1]),
                            int(angles[2]),
                            int(angles[3]),
                            int(angles[4]),
                        )
                        return
                    if para[0] == "get_motion":
                        motion_num = int(para[1])
                        name, mode = robo.get_motion(motion_num)
                        if name == "":
                            tx_str = "rm end,,"
                        elif mode == "":
                            tx_str = "rm " + str(motion_num) + ',' + str(name) + ',s'
                        else:
                            tx_str = "rm " + str(motion_num) + ',' + str(name) + ',r'
                        print(tx_str)
                        p.send(tx_str)
                        return
            if len(cmd) > 4:
                if cmd[0] == "m":       # Motion command
                    n = int(cmd[1:4])   # Get motion number
                    if n == 0:
                        robo._motions_str = cmd[4:] # Initialize motion string
                    else:
                        robo._motions_str = robo._motions_str + cmd[4:] # Append to motion string
                    p.send(cmd)
            elif cmd == "mend": # Motion end command
                robo.set_motions(robo._motions_str)
                p.send(cmd)
            elif cmd == "merr": # Motion error reset command
                robo._motions_str = ""
                p.send(cmd)

    p.on_write(on_rx)

    while True:
        if p.is_connected():
            led.on()
        else:
            led.off()


if __name__ == "__main__":
    main()
