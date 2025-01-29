# micropython_pranje_laktofriza

## custom front
clone (micropython-font-to-py)[https://github.com/peterhinch/micropython-font-to-py]
create custom font with `python font_to_py.py -x -k charsets/extended /usr/share/fonts/TTF/DejaVuSansMono.ttf 48 font48.py`\
copy `writer/writer.py` and `font48.py` to your project

usage:

```python
from machine import Pin, SPI
from pico_oled_1_3_spi import OLED_1inch3
from writer import Writer
import font32

spi_oled = SPI(1, 20_000_000, polarity = 0, phase = 0, sck = Pin(common_pins.OLED_SPI_SCK.id), mosi = Pin(common_pins.OLED_SPI_MOSI.id), miso = None)
oled = OLED_1inch3(spi = spi_oled, dc = Pin(common_pins.OLED_SPI_DC.id, Pin.OUT), cs = Pin(common_pins.OLED_SPI_CS.id, Pin.OUT), rst = Pin(common_pins.OLED_RST.id, Pin.OUT))
wri = Writer(oled, font32)
oled.text(f"MODE: FRIG", 4, 0, 0xFFFF)
oled.text(f"WIFI: no_conn", 4, 1 * (8 + 2), 0xFFFF)
oled.text(f" RSSI: -23", 4, 2 * (8 + 2), 0xFFFF)
wri.set_textpos(oled, 32, 4)
wri.printstring(f"-1.9{chr(176)}C")
oled.show()
```
