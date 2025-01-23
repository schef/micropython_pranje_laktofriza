import uasyncio as asyncio
import machine
from phy_interface import lights, rollos
import lan

async def action():
    reboot_confirmation = 0
    while True:
        if lan.reboot_requested:
            ready_list = []
            for key in rollos:
                rollo = rollos[key]
                ready_list.append(bool(rollo.up.active))
                ready_list.append(bool(rollo.down.active))
            for key in lights:
                light = lights[key]
                ready_list.append(bool(light.state))
            if not any(ready_list):
                reboot_confirmation += 1
                print(f"[RBT] reboot condition meet {reboot_confirmation}")
            if reboot_confirmation >= 2:
                print("[RBT] reboot in progress")
                machine.reset()
        await asyncio.sleep_ms(10000)
