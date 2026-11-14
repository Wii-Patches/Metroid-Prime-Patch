# hook: WPADGetInfoAsync(chan, info, callback), its first instruction.
#
# Every few seconds the game asks WPAD for the controller's state (battery level
# above all) and shows "Warning: Wii Remote Batteries" when it reads low.  With no
# Wii Remote, WPAD answers -1 and never fills the WPADInfo, so the game sees an
# empty battery.  While the GameCube pad is the reported controller on channel 0
# (gc_frame.s, PSTATE+9) and no Wii Remote is there, answer for it instead: a full
# battery, the extension attached, then callback(chan, 0) and return 0.
#
#   WPADInfo: +0 dpd, +4 speaker, +8 attach, +0xC lowBat, +0x10 nearempty (BOOLs),
#             +0x14 battery (0-4), +0x15 led, +0x16 protocol, +0x17 firmware
    cmplwi  3, 0
    bne     9f
    lis     6, PSTATE@ha
    lbz     6, (PSTATE+9)@l(6)
    cmpwi   6, 0
    beq     9f                          # the pad is not the reported controller
    lis     6, WTBL@ha
    lwz     6, WTBL@l(6)
    cmpwi   6, 0
    beq     9f
    lwz     6, WSTAT(6)
    cmpwi   6, -1
    bne     9f                          # a Wii Remote is connected: ask it
    cmpwi   4, 0
    beq     1f
    li      0, 0
    stw     0, 0x00(4)                  # dpd off
    stw     0, 0x04(4)                  # speaker off
    stw     0, 0x0c(4)                  # not low
    stw     0, 0x10(4)                  # not nearly empty
    stw     0, 0x14(4)                  # battery/led/protocol/firmware cleared
    li      0, 1
    stw     0, 0x08(4)                  # extension attached
    stb     0, 0x15(4)                  # led 1
    li      0, 4
    stb     0, 0x14(4)                  # battery full
1:  cmpwi   5, 0
    beq     2f
    mflr    0
    stwu    1, -0x10(1)
    stw     0, 0x14(1)
    mtctr   5
    li      4, 0                        # WPAD_ERR_NONE
    bctrl                               # callback(0, 0)
    lwz     0, 0x14(1)
    mtlr    0
    addi    1, 1, 0x10
2:  li      3, 0
    blr
9:
    .long   DISPLACED                   # displaced instruction (stwu r1,-N(r1))
