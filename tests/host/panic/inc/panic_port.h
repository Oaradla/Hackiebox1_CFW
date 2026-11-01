/*
 * panic_port.h for the host test of panic.c: the two retained words in
 * variables of the harness.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#ifndef PANIC_PORT_H
#define PANIC_PORT_H

#include <stdbool.h>
#include <stdint.h>

#define START_POWER_ON 0u
#define START_CORE_RESET 3u
#define START_MCU_RESET 4u
#define START_WDT_RESET 5u

extern uint32_t retained[2];
extern unsigned reset_cause;

static inline uint32_t port_irq_save(void) { return 0; }
static inline void port_irq_restore(uint32_t pm) { (void)pm; }
static inline bool port_in_isr(void) { return false; }
static inline unsigned port_reset_cause(void) { return reset_cause; }

static inline void port_retained_read(uint32_t *w1, uint32_t *w2)
{
    *w1 = retained[0];
    *w2 = retained[1];
}

static inline void port_retained_write(uint32_t w1, uint32_t w2)
{
    retained[0] = w1;
    retained[1] = w2;
}

#endif
