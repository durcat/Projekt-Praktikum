"""Empfängt die IMU-Daten vom XIAO per Bluetooth (Nordic UART Service),
zeigt sie live im Terminal an und speichert sie optional als CSV.

    python ble_empfang.py                 # nur anzeigen
    python ble_empfang.py messung1.csv    # anzeigen + speichern

Beenden mit Ctrl+C.
"""
import asyncio
import csv
import sys
import time

from bleak import BleakClient, BleakScanner

GERAETENAME = "XIAO-IMU"
# Nordic UART Service: das Board sendet über die TX-Characteristic
UART_TX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


async def main(csv_pfad=None):
    datei = open(csv_pfad, "w", newline="") if csv_pfad else None
    writer = csv.writer(datei) if datei else None
    if writer:
        writer.writerow(["t_s", "ax", "ay", "az", "gx", "gy", "gz"])

    puffer = ""
    t0 = None

    def bei_daten(_, data: bytearray):
        # BLE schickt Pakete von max. ~20 Byte, Zeilen kommen also zerstückelt an
        nonlocal puffer, t0
        puffer += data.decode(errors="ignore")
        while "\n" in puffer:
            zeile, puffer = puffer.split("\n", 1)
            zeile = zeile.strip()
            if not zeile:
                continue
            if t0 is None:
                t0 = time.monotonic()
            t = time.monotonic() - t0
            print(f"{t:8.3f}  {zeile}")
            if writer:
                writer.writerow([f"{t:.3f}", *zeile.split(",")])

    try:
        while True:
            print(f"Suche nach {GERAETENAME} ...")
            geraet = await BleakScanner.find_device_by_name(GERAETENAME, timeout=10)
            if geraet is None:
                print("Nicht gefunden (Board an? Akku geladen?), neuer Versuch.")
                continue

            getrennt = asyncio.Event()
            async with BleakClient(geraet, disconnected_callback=lambda _: getrennt.set()) as client:
                print(f"Verbunden mit {geraet.name} ({geraet.address})")
                await client.start_notify(UART_TX, bei_daten)
                await getrennt.wait()
            print("Verbindung verloren, verbinde neu ...")
    finally:
        if datei:
            datei.close()
            print(f"Gespeichert in {csv_pfad}")


if __name__ == "__main__":
    try:
        asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None))
    except KeyboardInterrupt:
        pass
