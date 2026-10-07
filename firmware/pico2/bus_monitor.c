/* SPDX-License-Identifier: GPL-3.0-or-later
 * Initial Pico 2 bring-up image. It NEVER drives the CPC data/reset pins.
 * Hardware ROM enable must remain OFF; no ROM image is served by this target.
 */
#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/clocks.h"
#include "board_pins.h"

#if !PICO_RP2350 || !defined(RASPBERRYPI_PICO2)
#error "Build for an original Pico 2 (RP2350)"
#endif

static uint32_t bus_output_mask(void) {
    uint32_t outputs = 0;
    for (unsigned gpio = 0; gpio < 30; ++gpio) {
        if (gpio_get_dir(gpio)) outputs |= UINT32_C(1) << gpio;
    }
    return outputs & PICOLINO_BUS_MASK;
}

int main(void) {
    gpio_init_mask(PICOLINO_BUS_MASK);
    gpio_set_dir_in_masked(PICOLINO_BUS_MASK);
    for (unsigned gpio = 0; gpio < 30; ++gpio) {
        if (PICOLINO_BUS_MASK & (UINT32_C(1) << gpio)) gpio_disable_pulls(gpio);
    }
    gpio_init(PICO_DEFAULT_LED_PIN);
    gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);
    stdio_init_all();
    unsigned count = 0;
    for (;;) {
        uint32_t sample = gpio_get_all();
        if ((count % 10) == 0) {
            printf("PICOLINO RP2350 monitor; ROM OFF; clock=%lu Hz\n",
                   (unsigned long)clock_get_hz(clk_sys));
        }
        printf("A=%04lx D=%02lx ROMEN=%u A15=%u LATCH=%u RESET=%u OE=%08lx\n",
               (unsigned long)(sample & PICOLINO_ADDRESS_MASK),
               (unsigned long)((sample & PICOLINO_DATA_MASK) >> PICOLINO_DATA_FIRST),
               (unsigned)((sample >> PICOLINO_ROMEN_GPIO) & 1),
               (unsigned)((sample >> PICOLINO_A15_GPIO) & 1),
               (unsigned)((sample >> PICOLINO_LATCH_GPIO) & 1),
               (unsigned)((sample >> PICOLINO_RESET_GPIO) & 1),
               (unsigned long)bus_output_mask());
        gpio_put(PICO_DEFAULT_LED_PIN, count++ & 1);
        sleep_ms(250);
    }
}
