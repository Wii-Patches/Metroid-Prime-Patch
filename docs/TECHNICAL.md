# How the patch works

Every Metroid Prime DOL (the two New Play Control! discs, both Metroid Prime 3
discs, and the four DOLs of each Trilogy disc) gets the same set of hooks. A hook
replaces one instruction with a branch to a short routine in a text section the
patcher adds at `0x80001820`; the routine runs the displaced instruction and
branches back. Sources are in `src/`, built per DOL by `tools/gen_prebuilt.py`
into `tools/prebuilt/*.json` (devkitPPC and the retail DOLs needed); the patcher
only reads the JSON.

All addresses below are Trilogy (USA) front end (`main.dol` / `rs5fe_p.dol`)
unless noted. Every other address is found per DOL by the generator, from the
DOL's own code, and the build stops if a match is not unique.

## Classic Controller (`cc`)

A Classic Controller on the Wii Remote is rewritten into the Wii Remote +
Nunchuk sample the game expects, inside KPAD's sampling callback (`cc_sample.s`):
left stick to Nunchuk stick, buttons to Wii Remote/Nunchuk bits, right stick to a
pointer position carried in the sample. `pointer.s` writes that position into the
KPAD status after KPAD finds no IR data.

## GameCube controller (`gc`)

### Why it needs more than a button mapping

- **Nothing polls the pad.** None of the DOLs link the `PAD` library. `si` is
  initialised at boot but nothing enables the Serial Interface's auto-polling, so
  on a real Wii the pad's answer never reaches `SIC0INBUFH` (`0xCD006404`).
  Dolphin fills that register whether or not the port is polled, so this does not
  show up in the emulator.
- **The game never asks KPAD without a Wii Remote.** The game's input update
  calls `KPADRead` only for a channel that WPAD's connect callback has reported as
  connected, and WPAD only reports Wii Remotes. With no remote, no KPAD hook ever
  runs.
- **It wants a Nunchuk.** The connect callback installs WPAD's extension
  callback. Until that callback reports a Nunchuk, the game treats the channel as
  a bare Wii Remote.
- **It checks the batteries.** Every few seconds the game asks
  `WPADGetInfoAsync` for the battery level. With no Wii Remote WPAD answers -1 and
  leaves the info empty, and the game warns "Wii Remote Batteries".

### Hooks

| Hook | Site | Source | Job |
| --- | --- | --- | --- |
| Frame | game input update, the instruction after its event-pump call (`0x80373178`) | `gc_frame.s` | SI poller; report the pad as connected / disconnected and as a Nunchuk |
| WPADProbe | first instruction (`0x804A6718`) | `gc_probe.s` | "connected, Nunchuk" while the pad answers and no Wii Remote is there |
| WPADGetInfoAsync | first instruction (`0x804A6A90`) | `gc_info.s` | while the pad is the reported controller and no Wii Remote is there: full battery, callback(chan, 0) |
| KPAD ring | `KPADRead`'s `lbz r0,0x10f(r31)` sample-count check (`0x804874A0`) | `gc_synth.s` (Trilogy Europe: `gc_synth_pal_mpt.s`) | no remote sample queued: build one from the pad |
| Sampling callback | `addi r0,r28,1` after the data-format store | `gc_sample.s` | a Wii Remote sample is overwritten with the pad's state |
| KPAD read loop | `b` after the per-sample IR call | `pointer.s` | C-stick to pointer |

`gc_convert.s` is the shared pad → Wii Remote + Nunchuk sample conversion: A fire,
B jump, Y missile (D-pad Down), X morph ball (D-pad Up), L lock-on (Z),
R fire, Z visor (Minus), Start pause (Plus), D-pad, control stick → Nunchuk stick,
C-stick → pointer.

### The frame hook

The game calls `KPADRead` from exactly one function, its input update; in every
DOL that function begins `… mr rN,r3 ; bl <event pump>` at `+0x30/+0x34`, and the
hook takes `+0x38`. Trilogy (Europe) calls a newer `KPADReadEx` through the SDK's
`li r6,0 ; li r7,0 ; b` wrapper. The hook runs once per frame on the game thread,
whether or not a controller is connected.

**SI poller** (`gc_poll.s`, the poller from the Barrel Blast and City Folk
patches, port 1 only):

- probe the port with `SIGetType` until `si`'s type cache says "standard pad", at
  most every 0.25 s;
- copy a persistent `NOREP` (pad unplugged) into the type cache, so the port is
  probed again when a pad comes back;
- every frame: poll command `0x00400300` into `SIC0OUTBUF`, `SISR` with WR plus
  the write-1-to-clear error bits, the port's enable + copy-on-vblank bits in
  `SIPOLL` and in `si`'s shadow of it (the VI retrace writes `SIPOLL` back from
  the shadow);
- force `si`'s busy channel idle after a second (a pad pulled mid-transfer
  wedges it).

`SIGetType`'s address is listed per DOL in `src/gen_common.py`; everything else
is read out of it: the `si` state block from its `lis/addi` of the type cache
(block = cache − 0x18; `+0` busy channel, `+4` SIPOLL shadow) and
`OSDisableInterrupts`/`OSRestoreInterrupts` from its first call (the three
interrupt helpers are checked word for word).

**Connect report.** WPAD's per-channel control blocks are found from
`WPADProbe` (the table it indexes, and the status it compares with -1, `+0x8BC`).
The connect callback is `0x18` before the status (`+0x8A4`), the extension
callback the word before that (`+0x8A0`), confirmed by the one function that swaps
a word there (`WPADSetConnectCallback`). While channel 0 has no Wii Remote:

- pad starts answering: `connect(0, 0)`, then `extension(0, 1)` (Nunchuk);
- pad stops answering: `connect(0, -1)`.

What was last reported is kept at `PSTATE+9`. With a Wii Remote connected WPAD
reports for itself, and the flag is cleared so the pad is reported again if the
remote goes away. In Trilogy (Europe) the game registers through
`KPADSetConnectCallback`, so WPAD's callback is KPAD's handler, which records the
connection and calls the game's.

`WPADGetInfoAsync` is the one function, other than `KPADRead`, that the input
update calls and that reads WPAD's control-block table and status.

### Patch state

`PSTATE` = `0x80002FE0`, 0x20 zero bytes in the injected section: `+0` time of
the last probe, `+4` when `si` was first seen busy, `+8` NOREP frame count, `+9`
what the frame hook last reported. Debug builds (`MP_DEBUG=1
tools/gen_prebuilt.py`) count events in `+0x11..+0x15` (samples made, probe calls,
probe answers faked, connect reports, frames), readable over Dolphin's GDB stub.

## Trilogy

The disc boots `sys/main.dol`, the game-select front end. It is byte-identical to
`files/rs5fe_p.dol`, which the games load to return to the menu, so both are
patched (as region `R3ME01`/`R3MP01`), along with `rs5mp1_p.dol`,
`rs5mp2_p.dol`, `rs5mp3_p.dol`.

## Testing

Verified in Dolphin only, with a GameCube pad on a pipe and **no Wii Remote**,
Trilogy (USA): strap screen, title, save, game select and main menu in the front
end (C-stick pointer, A), then Single Player → Metroid Prime 2 → difficulty, which
loads the patched `rs5mp2_p.dol`; its hooks report the pad and feed KPAD from the
first frame. In Metroid Prime 2's first room the control stick walks, the C-stick
turns, B jumps, A fires (KPAD channel 0 reads A as `0x0800` and the Nunchuk stick at
1.0 while held). "Nunchuk is required." shows once after the save screen; the
unpatched game shows it too with an emulated Wii Remote + Nunchuk.

Single Player → Metroid Prime → Normal loads the patched `rs5mp1_p.dol` the same
way. KPAD channel 0 reads A as `0x0800`, B as `0x0400` and the Nunchuk stick at 1.0
from the opening cutscene on. On the frigate's landing deck the control stick
walks, the C-stick turns, B jumps and A fires.

Single Player → Metroid Prime 3 → Normal loads the patched `rs5mp3_p.dol`. In the
gunship's cockpit the C-stick moves the aiming reticle and pans the view, A
interacts (the message screen, the radio buttons) and B backs out of a close-up.
On-foot play on the Olympus comes after the radio code puzzle and was not reached.

The pointer is absolute (C-stick position → screen position), but the front-end
menus smooth it heavily, so it takes about a second to settle where the stick
points.

Not tested on a real Wii. The poller is the one that works on hardware in the
Barrel Blast patch, but this game's use of it is not hardware-verified.

Patched discs need the USB loader's cheats, hook type and debugger turned off: a
Gecko code handler loads into the same low memory (`0x80001800`) as the patch.
