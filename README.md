# Paython-Serial-to-MSFS-SimConnect
Serial Port to Simconnect for Microsoft Flight Simulator 2020.

Serial 1 is main port for rotary encoders from esp32.
Serial 2 will be used for all sorts of buttons and switches.

Program automatically waits for MSFS to fully start.

Serial messages are UTF-8 encoded and have to be terminated by '\n'.
Can also contain '\r' which gets discarded automatically.

May not work reliable as it is still in development.

Tested only on GA aircraft up to the CJ4.
May not or only partially work on airliners.

