# Keep the Serial Interface polling GameCube port 1.  Included at the top of the
# WPADProbe hook (CHAN = the register holding the channel); runs for channel 0
# only, so about once per frame.  Scratch: r0, r3-r12, CTR, LR.  Calls go through CTR so the
# routine also works where a Gecko code handler places it.
#
# None of the Metroid Prime DOLs link the PAD library: `si` is initialised at boot,
# but nothing ever switches the hardware auto-poll on, so on a real Wii the pad's
# answer never reaches SIC0INBUFH (Dolphin fills the register whether or not the
# port is polled, which hides this).  This does what PADInit/PADRead would:
#
#   - probe the port with SIGetType until si's type cache says "standard pad",
#     at most every 0.25 s (probing every frame collides with the polling);
#   - copy a persistent NOREP (pad unplugged) into the type cache, so the port is
#     probed again when a pad is plugged back in (nothing else reads SISR);
#   - every frame: the poll command into SIC0OUTBUF, SISR with WR (latches it)
#     plus the write-1-to-clear error bits, the port's enable + copy-on-vblank bits
#     in SIPOLL and in si's shadow of it (the VI retrace writes SIPOLL back from
#     the shadow);
#   - si's "transfer in progress" channel stays wedged if a pad is pulled
#     mid-transfer: force it idle after a second.
#
# The same poller as the Barrel Blast patch (hardware-tested there) and the City
# Folk GameCube pad patch.
#
#   SIBASE   si's state: +0 the channel being transferred (-1 = idle),
#            +4 the SIPOLL shadow, +0x18 the four cached device types
#   PSTATE   0x20 bytes this patch owns: +0 time of the last probe,
#            +4 when si was first seen busy (0 = idle), +8 NOREP frame count
#            (+9 is gc_frame.s's, +0x10.. debug counters)
    cmplwi  CHAN, 0
    bne     .Lpoll_end
    lis     11, SIBASE@ha
    addi    11, 11, SIBASE@l
    lis     10, PSTATE@ha
    addi    10, 10, PSTATE@l
    lwz     3, 0x18(11)                 # port 1's cached type
    andi.   0, 3, 0x80
    bne     .Lpoll_probe                # unknown / probe pending
    rlwinm  0, 3, 0, 3, 4
    lis     4, 0x0800
    cmpw    0, 4
    beq     .Lpoll_norep                # a standard pad is known: no probe
.Lpoll_probe:
    mftb    5
    lwz     6, 0(10)
    subf    6, 6, 5
    lis     7, 0x00E7
    ori     7, 7, 0xBE2C                # 15187500 ticks = 0.25 s
    cmplw   6, 7
    blt     .Lpoll_norep
    stw     5, 0(10)
    li      3, 0
    lis     12, SIGETTYPE@ha
    addi    12, 12, SIGETTYPE@l
    mtctr   12
    bctrl                   # starts an asynchronous type probe
    lis     11, SIBASE@ha
    addi    11, 11, SIBASE@l
    lis     10, PSTATE@ha
    addi    10, 10, PSTATE@l
.Lpoll_norep:
    lis     9, 0xCD00
    lwz     8, 0x6438(9)                # SISR
    andis.  0, 8, 0x0800                # NOREP on port 1
    beq     .Lpoll_rep
    lbz     5, 8(10)
    cmplwi  5, 10
    bge     .Lpoll_gone
    addi    5, 5, 1
    stb     5, 8(10)
    b       .Lpoll_arm
.Lpoll_gone:
    li      5, 8
    stw     5, 0x18(11)                 # cached type = no response: SIGetType probes again
    b       .Lpoll_arm
.Lpoll_rep:
    li      5, 0
    stb     5, 8(10)
.Lpoll_arm:
    lis     5, 0x0040
    ori     5, 5, 0x0300
    stw     5, 0x6400(9)                # SIC0OUTBUF: poll, analog mode 3
    lis     5, 0x0F0F
    ori     5, 5, 0x0F0F
    and     5, 8, 5
    oris    5, 5, 0x8000
    stw     5, 0x6438(9)                # SISR: clear the error bits, WR latches OUTBUF
    li      4, 0
    lwz     3, 0x18(11)
    andi.   0, 3, 0x80
    bne     .Lpoll_set
    rlwinm  0, 3, 0, 3, 4
    lis     5, 0x0800
    cmpw    0, 5
    bne     .Lpoll_set
    li      4, 0x88                     # EN0 + VBCPY0 once a standard pad is known
.Lpoll_set:
    lwz     5, 0x6430(9)
    rlwinm  5, 5, 0, 0, 23
    andi.   0, 5, 0xFF00
    bne     .Lpoll_y
    ori     5, 5, 0x0100                # Y = 1 poll per frame if si left it unset
.Lpoll_y:
    or      5, 5, 4
    stw     5, 0x6430(9)                # SIPOLL
    lwz     5, 4(11)
    rlwinm  5, 5, 0, 0, 23
    or      5, 5, 4
    stw     5, 4(11)                    # si's SIPOLL shadow
    lwz     5, 0(11)
    cmpwi   5, -1
    bne     .Lpoll_busy
    li      5, 0
    stw     5, 4(10)                    # si idle
    b       .Lpoll_end
.Lpoll_busy:
    mftb    6
    lwz     7, 4(10)
    cmpwi   7, 0
    bne     .Lpoll_wait
    ori     6, 6, 1
    stw     6, 4(10)                    # first seen busy now
    b       .Lpoll_end
.Lpoll_wait:
    subf    7, 7, 6
    lis     5, 0x039E
    ori     5, 5, 0xF8B0                # 60750000 ticks = 1 s
    cmplw   7, 5
    blt     .Lpoll_end
    lis     12, OSDISABLE@ha
    addi    12, 12, OSDISABLE@l
    mtctr   12
    bctrl
    lis     11, SIBASE@ha
    addi    11, 11, SIBASE@l
    li      5, -1
    stw     5, 0(11)                    # si idle again
    lis     9, 0xCD00
    lis     5, 0x8000
    stw     5, 0x6434(9)                # SICOMCSR: clear the transfer
    lis     12, OSRESTORE@ha
    addi    12, 12, OSRESTORE@l
    mtctr   12
    bctrl                   # r3 = the level OSDisableInterrupts returned
    lis     10, PSTATE@ha
    addi    10, 10, PSTATE@l
    li      5, 0
    stw     5, 4(10)
.Lpoll_end:
