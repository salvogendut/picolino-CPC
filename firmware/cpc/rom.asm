; SPDX-License-Identifier: GPL-3.0-or-later
; Background ROM for PicoROM (or any CPC ROM box). Run |CYBUSB.
        org &c000
        db 1,0,1,0
        dw names
        jp init
        jp diagnostic
names:  db 'CYBOARD USB PO','C'+128
        db 'CYBUS','B'+128,0
init:   push af
        push bc
        push de
        push hl
        ld hl,rom_banner
        call print_string
        pop hl
        pop de
        pop bc
        pop af
        scf
        ret
rom_banner:
        db ' Cyboard USB POC: |CYBUSB',13,10,0
        include 'diagnostic.inc'
        assert $ <= &10000
        defs &10000-$,&ff
