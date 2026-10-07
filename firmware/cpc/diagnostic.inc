; SPDX-License-Identifier: GPL-3.0-or-later
; CH376 parallel protocol, FE80/FE81. Registers hold all mutable state, so
; this code can run in ROM. No INIR/OTIR: those would change high port bits.
; Return carry clear/A=0 on success, carry set/A=error on failure.
CH_DATA equ &fe80
CH_CMD equ &fe81
TXT_OUTPUT equ &bb5a
TIMEOUT equ &ff
MISMATCH equ &e1
BAD_LENGTH equ &e2
ifndef WAIT_POLLS
WAIT_POLLS equ 65535
endif
ifndef WAIT_ROUNDS
WAIT_ROUNDS equ 4
endif
ifndef RESET_LOOPS
RESET_LOOPS equ 12000
endif

diagnostic:
        push ix
        push iy
        call run_diagnostic
        pop iy
        pop ix
        ret

run_diagnostic:
        ld hl,banner
        call print_string
        ld a,&05                  ; RESET_ALL
        call write_command
        jp c,failed
        call reset_delay          ; >35 ms on a standard 4 MHz CPC
        ld hl,detect_message
        call print_string
        ld a,&55
        call check_exist
        jp c,failed
        ld a,&aa
        call check_exist
        jp c,failed
        ld hl,ok_message
        call print_string

        ld hl,version_message
        call print_string
        ld a,&01                  ; GET_IC_VER
        call write_command
        jp c,failed
        call read_data
        call print_hex
        call newline

        ld hl,connect_message
        call print_string
        ld a,5                    ; host, detect attachment without SOF
        call set_mode
        jp c,failed
        call wait_interrupt
        jp c,failed
        cp &15                    ; USB_INT_CONNECT
        jp nz,failed
        ld a,7                    ; assert USB bus reset
        call set_mode
        jp c,failed
        call reset_delay
        ld a,6                    ; release reset, generate SOF
        call set_mode
        jp c,failed
        call reset_delay
        ld a,&22                  ; clear any attach/reset notification
        call write_command
        jp c,failed
        call read_data
        ld hl,ok_message
        call print_string

        ld hl,mount_message
        call print_string
        ld e,10                   ; some drives need repeated DISK_MOUNT
mount_retry:
        ld a,&31
        call command_interrupt
        jp c,failed
        cp &14                    ; USB_INT_SUCCESS
        jr z,mounted
        cp &16                    ; disconnected
        jp z,failed
        dec e
        jp z,failed
        call reset_delay
        jr mount_retry
mounted:
        ld hl,ok_message
        call print_string
        ld hl,open_message
        call print_string
        ld a,&2f                  ; SET_FILE_NAME
        call write_command
        jp c,failed
        ld hl,filename
filename_loop:
        ld a,(hl)
        call write_data
        inc hl
        or a
        jr nz,filename_loop
        ld a,&32                  ; FILE_OPEN
        call command_interrupt
        jp c,failed
        cp &14
        jp nz,failed
        ld hl,ok_message
        call print_string

        ld hl,read_message
        call print_string
        ld a,&3a                  ; BYTE_READ, fixture length
        call write_command
        jp c,file_failed
        ld a,expected_end-expected
        call write_data
        xor a
        call write_data
        ld hl,expected
        ld de,expected_end-expected
read_next:
        call wait_interrupt
        jp c,file_failed
        cp &14
        jr z,read_complete
        cp &1d                    ; USB_INT_DISK_READ
        jp nz,file_failed
        ld a,&27                  ; RD_USB_DATA0: length then bytes
        call write_command
        jp c,file_failed
        call read_data
        or a
        jr z,length_failed
        ld b,a
read_chunk:
        ld a,d
        or e
        jr z,length_failed
        call read_data
        cp (hl)
        jr nz,compare_failed
        inc hl
        dec de
        djnz read_chunk
        ld a,&3b                  ; BYTE_RD_GO (must complete the transfer)
        call write_command
        jp c,file_failed
        jr read_next
read_complete:
        ld a,d
        or e
        jr nz,length_failed
        ld a,&3a                  ; demand EOF; catch a longer wrong fixture
        call write_command
        jr c,file_failed
        ld a,1
        call write_data
        xor a
        call write_data
        call wait_interrupt
        jr c,file_failed
        cp &14
        jr nz,length_failed
        call close_file
        jp c,failed
        cp &14
        jp nz,failed
        ld hl,pass_message
        call print_string
        xor a
        ret
compare_failed:
        ld a,MISMATCH
        jr file_failed
length_failed:
        ld a,BAD_LENGTH
file_failed:
        push af
        call close_file           ; update flag=0, including on failure
        pop af
failed:
        push af
        ld hl,fail_message
        call print_string
        pop af
        call print_hex
        call newline
        scf
        ret

check_exist:
        push de
        ld e,a
        ld a,&06
        call write_command
        jr c,check_return
        ld a,e
        call write_data
        call read_data
        cpl
        cp e
        jr z,check_return
        ld a,MISMATCH
        scf
check_return:
        pop de
        ret

set_mode:
        push de
        push hl
        ld e,a
        ld a,&15
        call write_command
        jr c,mode_return
        ld a,e
        call write_data
        ld hl,WAIT_POLLS
mode_poll:
        call read_data
        cp &51
        jr z,mode_return
        cp &5f
        jr z,mode_abort
        dec hl
        ld a,h
        or l
        jr nz,mode_poll
        ld a,TIMEOUT
mode_abort:
        scf
mode_return:
        pop hl
        pop de
        ret

close_file:
        ld a,&36
        call write_command
        ret c
        xor a                     ; do NOT update directory/file metadata
        call write_data
        jp wait_interrupt

command_interrupt:
        call write_command
        ret c
wait_interrupt:
        push bc
        push de
        push hl
        ld bc,CH_CMD
        ld d,WAIT_ROUNDS
irq_round:
        ld hl,WAIT_POLLS
irq_poll:
        in a,(c)
        and &90                   ; command engine ready AND IRQ pending
        jr z,irq_ready
        dec hl
        ld a,h
        or l
        jr nz,irq_poll
        dec d
        jr nz,irq_round
        ld a,TIMEOUT
        scf
        jr irq_return
irq_ready:
        ld a,&22                  ; GET_STATUS acknowledges interrupt
        out (c),a
        dec c                     ; FE80, preserve high address bits
        in a,(c)
        or a
irq_return:
        pop hl
        pop de
        pop bc
        ret

write_command:
        push bc
        push de
        push hl
        ld e,a
        ld bc,CH_CMD
        ld hl,WAIT_POLLS
command_poll:
        in a,(c)
        bit 4,a
        jr z,command_ready
        dec hl
        ld a,h
        or l
        jr nz,command_poll
        ld a,TIMEOUT
        scf
        jr command_return
command_ready:
        ld a,e
        out (c),a
        or a
command_return:
        pop hl
        pop de
        pop bc
        ret
write_data:
        push bc
        ld bc,CH_DATA
        out (c),a
        pop bc
        ret
read_data:
        push bc
        ld bc,CH_DATA
        in a,(c)
        pop bc
        ret

reset_delay:
        push af
        push hl
        ld hl,RESET_LOOPS
delay_loop:
        dec hl
        ld a,h
        or l
        jr nz,delay_loop
        pop hl
        pop af
        ret
print_string:
        ld a,(hl)
        or a
        ret z
        call putchar
        inc hl
        jr print_string
putchar:
        push af
        push bc
        push de
        push hl
        call TXT_OUTPUT
        pop hl
        pop de
        pop bc
        pop af
        ret
print_hex:
        push af
        rrca
        rrca
        rrca
        rrca
        call print_nibble
        pop af
        push af
        call print_nibble
        pop af
        ret
print_nibble:
        and 15
        add a,'0'
        cp '9'+1
        jr c,hex_digit
        add a,7
hex_digit:
        jp putchar
newline:
        push af
        ld a,13
        call putchar
        ld a,10
        call putchar
        pop af
        ret

banner: db 13,10,'Cyboard CH376 read-only POC',13,10,0
detect_message: db 'Detect: ',0
version_message: db 'Chip version: ',0
connect_message: db 'USB connect: ',0
mount_message: db 'Mount: ',0
open_message: db 'Open /CYBOARD.TXT: ',0
read_message: db 'Verify complete file: ',0
ok_message: db 'OK',13,10,0
pass_message: db 'PASS',13,10,0
fail_message: db 'FAIL status=',0
filename: db '/CYBOARD.TXT',0
expected:
        incbin 'CYBOARD.TXT'
expected_end:
        assert expected_end-expected > 64
        assert expected_end-expected < 256
