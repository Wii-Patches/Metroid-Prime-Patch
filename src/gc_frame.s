# hook: the game's input update (the one caller of KPADRead), the instruction
# right after its event-pump call -- once per frame on the game's main thread;
# r0, r3-r12 and the volatile FPRs are free.  The displaced instruction (a load,
# different per DOL) is DISPLACED.
#
# Two jobs that need a frame tick of their own, because with no Wii Remote the
# game never reaches KPAD:
#
#   - the SI poller (gc_poll.s), so the pad answers at all on a real Wii;
#   - "a controller connected": the game's input manager only calls KPADRead for
#     a channel once WPAD's connect callback has told it a controller connected
#     (the game registers it directly, or, in Trilogy Europe, through KPAD, whose
#     own handler WPAD then calls).  WPAD only does that for a Wii Remote, so while
#     channel 0 has no Wii Remote (its WPAD status is -1), report the pad the same
#     way: callback(0, 0) when it starts answering, callback(0, -1) when it stops.
#     PSTATE+9 remembers what was last reported.  While a Wii Remote is connected
#     WPAD reports for itself; the flag is cleared so the pad is reported again if
#     the remote goes away.
#   - right after "connected", the extension: the game sets WPAD's extension
#     callback from its connect callback and refuses to play ("Nunchuk is
#     required.") until it reports a Nunchuk, so call it with (0, 1).
#
#   WTBL     WPAD's table of per-channel control blocks
#   WSTAT    offset of the channel status in a block (-1 = no Wii Remote)
#   WCB      offset of the connect callback in a block; the extension callback
#            is the word before it
    li      3, 0
    .set    CHAN, 3
#include gc_poll.s
    dbg     0x15
    lis     7, PSTATE@ha
    addi    7, 7, PSTATE@l
    lis     10, WTBL@ha
    lwz     10, WTBL@l(10)              # channel 0's WPAD control block
    cmpwi   10, 0
    beq     9f
    lwz     0, WSTAT(10)
    cmpwi   0, -1
    beq     1f
    li      0, 0
    stb     0, 9(7)                     # a Wii Remote is connected: WPAD reports it
    b       9f
1:  li      6, 0
    lis     9, 0xCD00
    lwz     8, 0x6404(9)                # SIC0INBUFH
    cmpwi   8, 0
    blt     2f                          # error / no pad
    andis.  0, 8, 0x0080
    beq     2f                          # not a pad response
    li      6, 1
2:  lbz     5, 9(7)
    cmpw    5, 6
    beq     9f                          # nothing changed
    lwz     0, WCB(10)
    cmpwi   0, 0
    beq     9f                          # the game has not set a callback yet
    stb     6, 9(7)
    dbg     0x14
    lwz     12, WCB(10)
    li      3, 0
    li      4, 0                        # 0 = connected
    cmpwi   6, 0
    bne     3f
    li      4, -1                       # -1 = no controller
3:  mtctr   12
    bctrl
    lis     7, PSTATE@ha
    lbz     0, (PSTATE+9)@l(7)
    cmpwi   0, 0
    beq     9f                          # that was the disconnect
    lis     10, WTBL@ha
    lwz     10, WTBL@l(10)
    lwz     12, WCB-4(10)               # the extension callback the game just set
    cmpwi   12, 0
    beq     9f
    li      3, 0
    li      4, 1                        # WPAD_DEV_FREESTYLE: a Nunchuk
    mtctr   12
    bctrl
9:
    .long   DISPLACED                   # displaced instruction
