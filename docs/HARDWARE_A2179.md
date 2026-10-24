# Hardware reference: MacBookAir9,1 (A2179)

Branch: `research/mba91-aks-ep7`
Status: schematic-derived, connector maps visually verified (2026-10-24)

Board-level facts behind the Touch ID work on this Air, plus the Wi-Fi/BT
module for completeness. Software narrative stays in
[`FINDINGS.md`](FINDINGS.md); this file is only about copper.

Everything marked **[sch]** comes from the repair-community schematics
`820-01958` (logic board, 86 pages, drawing `051-05232`, rev `2.0.0`) and
`820-01992` (RIO/audio board, 7 pages, drawing `051-05325`). **[host]** is
this machine. Those PDFs are **not** committed here — see
[Provenance](#provenance).

---

## 1. Three boards, two flexes

```
logic board 820-01958   (181 x 44.98 mm, 3,456 components, 2,199 nets)
  U3900  T2 "Gibraltar" + Secure Enclave
  U3701  Wi-Fi/BT "Sapporo"
  J6100  RIO interposer, 50-pin, Molex 502250-8045
        |
        |  flex 518S00155 (supplier 998-11285, on X1032 RIO flex J0200)
        |
RIO / audio board 820-01992   (service P/N reported 923-03986 / 923-03987)
  J0600  interposer, 48-pin, Hirose BM28P0.6-44DS-0.35V
  J0602  Mesa sensor, 16-pin, Molex 505066-1222
  J0601  right speaker, 7-pin, 78171-0005, cable 518S0588
        |
        |  sensor flex APN 516S00203
        |
Touch ID button + sensor in the top case
  service P/N 661-15412, flex 821-02630-01
```

The sensor is on the audio board because the button lives in the top case
next to the right speaker. RIO generates the sensor's three rails locally
and passes SPI back to the logic board.

---

## 2. Touch ID chain

### 2.1 J0602 — sensor-side connector (RIO board)

Verified against a rendered page, not text extraction:

| Pin | Net |
| ---: | --- |
| 1 | `PP1V8_MESA_CONN` |
| 2 | `SPI_MESA_MISO_CONN` |
| 3 | GND |
| 4 | `MESA_INT_CONN` |
| 5 | `PMU_ONOFF_CONN_L` |
| 6 | `MESA_BOOST_EN_CONN` |
| 7 | `SPI_MESA_MOSI_CONN` |
| 8 | GND |
| 9 | `SPI_MESA_CLK_CONN` |
| 10 | GND |
| 11 | `PP16V0_MESA_CONN` |
| 12 | GND |
| 13, 14 (shell) | `PP3V0_MESA_CONN` |
| 15, 16 (shell) | GND |

There is **no chip select**. The sensor is the only device on that SPI
segment, so the T2 selects it by owning the bus. Any capture or replay on
this bus is therefore unambiguous.

### 2.2 Rails and sequencing (RIO page 2)

Required order is printed on the drawing: **1V8 → 3V3 → 16V0**. The order
is enforced in hardware, not firmware:

| Rail | Part | Input | Enable |
| --- | --- | --- | --- |
| `PP1V8_MESA` | `U0220` LP5907SNX-1.825 LDO, 1.5 mA | `PP3V3_G3S` | `MESA_PWR_EN` |
| `PP3V0_MESA` | `U0210` NCP160AMX300 switch, 100 mA | `PP3V3_G3S` | **`PP1V8_MESA`** |
| `PP16V0_MESA` | `U0200` LM3638A0 boost, 12.5 mA | `PP3V3_G3S` via `L0201` | `MESA_BOOST_EN` (EN_S) + `MOJAVE_EN_M` |

The 3.0 V switch's enable pin is tied to the 1.8 V rail, so 3.0 V cannot
precede 1.8 V. The 16 V block is labelled "MOJAVE 16V BOOST"; `EN_M`/`EN_S`
are reached through 0 Ω options `R0215`/`R0216`, and the output passes
through `FL0200` (80 Ω @ 100 MHz, 500 mA) to become `PP16V0_MESA_CONN`.

`PP16V0_MESA` is the sensor's high-voltage supply and is current-limited to
~12.5 mA. It sags under any external load, so do not hang a probe or a
resistor divider on it and expect the sensor to keep working.

### 2.3 J6100 — logic-board side of the interposer

Verified against a rendered page. All grounds are one rail per side, both
terminating in ground symbols:

| Pins | Net |
| --- | --- |
| 1, 2, 3, 4, 5, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49 | GND (46/48 and 47/49 are shell lugs) |
| 6 | `PP1V8_SLPS2R` |
| 7, 8 | `PP3V3_G3S_G3H_RIO` |
| 9 | `PP1V8_G3S` |
| 10 | `CODEC_RESET_L` |
| 11 | `CODEC_INT_L` |
| 12 | `CODEC_WAKE_L` |
| 13 | `SPKR_ID1` |
| 14 | `I2C_SPKRAMP_R_SDA` |
| 15 | `I2C_SPKRAMP_R_SCL` |
| 16 | `I2S_CODEC_D2R` |
| 17 | `I2S_CODEC_BCLK` |
| 18 | `AUD_PWR_EN` |
| 19 | `I2S_CODEC_R2D` |
| 20 | `I2S_CODEC_LRCLK` |
| **21** | **`SPI_MESA_MISO`** |
| **22** | **`MESA_INT`** |
| 23 | `PMU_ONOFF_R_L_CONN` |
| **24** | **`SPI_MESA_MOSI`** |
| **25** | **`SPI_MESA_CLK`** |
| **26** | **`MESA_PWR_EN`** |
| 27 | `SMC_LID_RIGHT` |
| 28 | `I2S_SPKRAMP_L_D2R` |
| 29 | `I2S_SPKRAMP_R_BCLK` |
| 30 | `I2S_SPKRAMP_R_R2D` |
| 31 | `I2S_SPKRAMP_R_LRCLK_R` |
| 32 | `SPKRAMP_INT_L` |
| 33 | `SPKRAMP_RESET_L` |
| 34 | NC |
| 35, 36, 37, 38, 39 | `PPBUS_G3H` |

`PP3V3_G3S_G3H_RIO` is made on the logic board by `R6101` (0 Ω) from
`PP3V3_G3H`, so RIO and its 3.3 V loads hang off the main 3.3 V always-on
rail.

### 2.4 J0600 — RIO side of the interposer

Odd pins on the left of the symbol, even on the right:

| Pin | Net | Pin | Net |
| ---: | --- | ---: | --- |
| 1, 2 | GND (tied to shell lugs 45/46) | — | — |
| 3 | `PPBUS_G3H` | 4 | `PPBUS_G3H` |
| 5 | `PPBUS_G3H` | 6 | `PPBUS_G3H` |
| 7 | `PPBUS_G3H` | 8 | GND |
| 9 | `SMC_LID_RIGHT` | 10 | GND |
| 11 | `MESA_PWR_EN` | 12 | GND |
| 13 | `SPI_MESA_CLK` | 14 | `SPKRAMP_RESET_L` |
| 15 | `SPI_MESA_MOSI` | 16 | `SPKRAMP_INT_L` |
| 17 | `MESA_MENUKEY_L` | 18 | `I2S_SPKRAMP_R_LRCLK_R` |
| 19 | `MESA_INT` | 20 | `I2S_SPKRAMP_R_R2D` |
| 21 | `SPI_MESA_MISO` | 22 | `I2S_SPKRAMP_R_BCLK` |
| 23 | `I2S_CODEC_LRCLK` | 24 | `I2S_SPKRAMP_L_D2R` |
| 25 | `I2S_CODEC_R2D` | 26 | `NC_SPKR_ID1` (`NO_TEST=1`) |
| 27 | `AUD_PWR_EN` | 28 | `CODEC_WAKE_L` |
| 29 | `I2S_CODEC_BCLK` | 30 | `CODEC_INT_L` |
| 31 | `I2S_CODEC_D2R` | 32 | `CODEC_RESET_L` |
| 33 | `I2C_RIO_SCL` | 34 | GND |
| 35 | `I2C_RIO_SDA` | 36 | GND |
| 37 | `PP1V8_G3S` | 38 | GND |
| 39 | `PP3V3_G3S` | 40 | GND |
| 41 | `PP3V3_G3S` | 42 | GND |
| 43 | `PP1V8_SLPS2R` | 44 | GND |
| 45, 46, 47, 48 (shell) | GND | | |

48 pins on the RIO end, 50 on the logic end. The signal set matches
exactly — **33 signals each**, same power distribution (5× `PPBUS_G3H`,
2× 3.3 V, 1× `PP1V8_G3S`, 1× `PP1V8_SLPS2R`) — but **the numbering is not
straight-through**. J0600 pin *n* does not land on J6100 pin *n*; a
boardview trace is needed for hop-by-hop continuity.

The port arrows on the drawing (`IN` / `OUT` / `BI`) are sheet-relative
flags, not reliable physical direction indicators. Use §2.5 instead.

### 2.5 Attachment to the T2

Logic-board page 33:

| Net | T2 ball | T2 pin |
| --- | --- | --- |
| `SPI_MESA_MISO` | **A19** | `SPI2_MISO` |
| `SPI_MESA_MOSI_R` | **A20** | `SPI2_MOSI` |
| `SPI_MESA_CLK_R` | **C19** | `SPI2_SCLK` |

No chip-select is routed to the sensor. `SPI2_SSIN` exists (ball `A18`)
but goes nowhere near Mesa; the touchpad's CS is on another controller
(`SPI_TPAD_CS_L` on `SPI1_SSIN`, ball `T32`).

`MESA_INT` is T2 `GPIO6` (ball `AC36`); `MESA_PWR_EN` is `GPIO7` (ball
`V34`). The T2 both powers and services the sensor. The Intel PCH never
sees it — which is why nothing about this bus appears in the PCH-facing
ACPI or in EP7.

### 2.6 Probing cheat sheet

| Want to see | Where |
| --- | --- |
| Sensor bus, easiest access | `J0602` pins 2/4/7/9 (MISO / INT / MOSI / CLK) on RIO |
| Sensor bus, logic side | `J6100` pins 21/22/24/25 |
| Power sequencing | `PP1V8_MESA` → `PP3V0_MESA` → `PP16V0_MESA`, all on RIO page 2 |
| Boost enable | `MESA_BOOST_EN` at `J0602` pin 6 |
| Master enable | `MESA_PWR_EN` at `J6100` pin 26 / `J0600` pin 11 |
| Button press | `PMU_ONOFF_CONN_L` (`J0602` pin 5) and `MESA_MENUKEY_L` (`J0600` pin 17) |

### 2.7 Why a sensor swap kills Touch ID

Apple's Platform Security guide states that the built-in sensor talks to
the Secure Enclave over SPI and that the session key is negotiated from a
shared secret **provisioned at the factory into that sensor and the
matching Secure Enclave**. Traffic is AES-key-wrapped and AES-CCM
protected; the SEP stores only encrypted templates.

So a replacement `661-15412` — even a genuine one — carries a different
secret and the T2 cannot open a session. The button keeps working because
it is just a switch on `PMU_ONOFF`/`MESA_MENUKEY_L`. Only Apple's
calibration flow re-pairs them. This is the hardware reason the Linux
work must reuse macOS-enrolled fingers, and why the Catacomb/SEP identity
mismatch in [`FINDINGS.md`](FINDINGS.md) is not a software bug we can
route around.

---

## 3. Wi-Fi / Bluetooth (context)

| Property | Value |
| --- | --- |
| Module | `U3701`, Murata `LBEE5XV1SA-255`, LGA451, Apple `339S00616` / `339S00628` / `339S00632` |
| Codename | `SAPPORO` ("SAPPORO - ES3.X") |
| Silicon | Broadcom `BCM4377b`, `14e4:4488` (Wi-Fi) / `14e4:5fa0` (BT), `106b:0870` rev `0x04` |
| Module instance | `fiji`, `M=SPPR m=3.1 V=m`, chip stepping `s=B3` |
| Link | PCIe **Gen2 ×1** (`IOPCIExpressLinkStatus` = `0x1012`) |
| Radio | 2×2 802.11ac, 80 MHz, no 6 GHz; BT 5.0; both over the one PCIe function |

Rails `PP3V3_G3S_WLANBT` (from `PP3V3_G3S`, `U8210`) and `PP1V8_G3S`
(`U8220`). Enables `WLAN_PWR_EN` → `WL_REG_ON`, and `BT_PWR_EN` →
`BT_REG_ON` with the schematic note *"BT_PWR_EN DISCONNECTED FOR BT OVER
PCIE"*. `BT_INTERFACE_SEL` strap: `LOW (default) = PCIE`, `HIGH = UART`.

Config storage: `U3710` 8-pin EEPROM holds the WLAN SROM (calibration, MAC,
regulatory) — the blob macOS surfaces as `Chip provisioning data → SROM`,
signature `Cw`, version `0x12`. `U3750` is an `MX25U4035FZUI` 4 Mbit SPI
NOR for Bluetooth.

Relevant to Linux: `brcmfmac` + `hci_bcm4377` both need firmware extracted
from a macOS install (`C-4377__s-B3/fiji.trx` plus hashstore). `wpa_supplicant`
≥ 2.11 needs `iwd` or `brcmfmac.feature_disable=0x82000`. BT and 2.4 GHz
Wi-Fi interfere.

---

## 4. Verification

Host-side:

```sh
ioreg -r -n AppleBCMWLANBusInterfacePCIe -l -w0 | grep -iE 'module-instance|srom'
ioreg -r -c IOPCIDevice -l -w0 | grep -B2 -A2 IOPCIExpressLinkStatus
system_profiler SPiBridgeDataType
```

Schematic-side (with the encrypted PDFs present locally):

```sh
python -c "
from pypdf import PdfReader
print(PdfReader('820-01958-schematic.pdf').pages[48].extract_text())  # J6100
print(PdfReader('820-01958-schematic.pdf').pages[32].extract_text())  # T2 SPI2 / Mesa
"
qlmanage -t -s 4000 -o . page49.pdf   # rasterise one page for visual checks
```

Text extraction alone mis-orders connector pins. Every pin table above was
confirmed against a rendered page image, not against `extract_text()`
output.

---

## Provenance

The `820-01958` and `820-01992` schematics are Apple-proprietary documents
that Apple does not publish. FCC ID `BCG-A2179` publishes internal photos
but withholds schematics, block diagrams and BOMs. The PDFs, boardview and
page rasters live outside this repo (`~/Projects/hardware-research/a2179/`)
and are deliberately not committed.

Sources: Apple Platform Security (biometric security, Touch ID channel
security), Apple tech specs, FCC `BCG-A2179`, iFixit MBA 2020 guides,
t2linux wiki, `drivers/bluetooth/hci_bcm4377.c`, and the repair-community
schematic archives.

## Open questions

1. J0600 → J6100 hop-by-hop continuity is unproven; needs a net trace in
   `820-01958.brd`.
2. The Mesa sensing die itself is unpublished; only module-level P/N
   `661-15412` and flex `516S00203` are known.
3. No Broadcom or Murata datasheet exists publicly for `BCM4377` or
   `LBEE5XV1SA-255`; silicon detail is inferred from net names, Apple
   drivers and `ioreg`.
4. `516S00038` is called out above `J0600` on the RIO drawing; whether it
   is the same interposer flex as `518S00155` or a distinct APN is unclear.
