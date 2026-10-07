/* SPDX-License-Identifier: GPL-3.0-or-later
 * GPIO numbering, not module contact numbering. See hardware/interfaces.json.
 * Retains the CPC_PICOROM signal allocation through external translation.
 */
#ifndef PICOLINO_BOARD_PINS_H
#define PICOLINO_BOARD_PINS_H
#include <stdint.h>
enum {
    PICOLINO_ADDRESS_FIRST = 0,
    PICOLINO_ADDRESS_COUNT = 14,
    PICOLINO_DATA_FIRST = 14,
    PICOLINO_DATA_COUNT = 8,
    PICOLINO_ROMEN_GPIO = 22,
    PICOLINO_A15_GPIO = 26,
    PICOLINO_LATCH_GPIO = 27,
    PICOLINO_RESET_GPIO = 28,
};
#define PICOLINO_ADDRESS_MASK UINT32_C(0x00003fff)
#define PICOLINO_DATA_MASK UINT32_C(0x003fc000)
#define PICOLINO_BUS_MASK (PICOLINO_ADDRESS_MASK | PICOLINO_DATA_MASK | \
    (UINT32_C(1) << PICOLINO_ROMEN_GPIO) | (UINT32_C(1) << PICOLINO_A15_GPIO) | \
    (UINT32_C(1) << PICOLINO_LATCH_GPIO) | (UINT32_C(1) << PICOLINO_RESET_GPIO))
_Static_assert((PICOLINO_ADDRESS_MASK & PICOLINO_DATA_MASK) == 0, "Bus pin overlap");
_Static_assert((PICOLINO_BUS_MASK & (UINT32_C(1) << 25)) == 0, "LED overlaps CPC bus");
#endif
