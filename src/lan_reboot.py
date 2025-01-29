import asyncio
import machine
import phy_interface
import wlan as lan

async def action():
    reboot_confirmation = 0
    while True:
        if lan.reboot_requested:
            ready_list = []
            ready_list.append(bool(phy_interface.washing_logic.in_progress()))
            if not any(ready_list):
                reboot_confirmation += 1
                print(f"[RBT] reboot condition meet {reboot_confirmation}")
            if reboot_confirmation >= 2:
                print("[RBT] reboot in progress")
                machine.reset()
        await asyncio.sleep_ms(10000)
