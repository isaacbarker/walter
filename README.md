## WALTER. _The automatic plant watering robot._

**About The Project**

WALTER is a automatic plant irrigation system that works using a Raspberry Pi PICO. The system includes a web interface to view changing soil moisture and see when watering last occured.

The circuit includes an OLED panel to view the last measured soil moisture and last water more directly. It consists of three sections: the OLED panel, the soil moisture sensor and the pump. 

**Setting up**

_TODO_ List of parts and circuit components.

- Pull the repository. Upload the `pico` folder to the pi pico and install a relevant sh1106 driver. Add a `config.py` formatted in the form of the `example.config.py`.

- Upload the `web` folder to a suitable device to run the web server. Install dependencies and add a `.env` file formatted in the form of the `example.env`

- Run the web server and then run the pico program. 


