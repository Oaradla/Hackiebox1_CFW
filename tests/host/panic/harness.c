/* Host test: the breakdown marker of the network processor's start as
 * panic.c reads it from the retained words.
 * SPDX-License-Identifier: GPL-3.0-or-later */
#include <stdarg.h>
#include <stdio.h>
#include "FreeRTOS.h"
#define FA_OPEN_ALWAYS 16
#define taskSCHEDULER_NOT_STARTED 1
static int xTaskGetSchedulerState(void) { return 0; }
static const char *pcTaskGetName(TaskHandle_t t)
{
    (void)t;
    return "";
}
static void vTaskSuspend(TaskHandle_t t) { (void)t; }
#include "panic.c"

uint32_t retained[2];
unsigned reset_cause;
static int failures;

uint8_t buildblock_slot(void) { return 1; }
void debug_printf(const char *f, ...)
{
    va_list a;
    va_start(a, f);
    printf("    | ");
    vprintf(f, a);
    va_end(a);
}

static void check(bool c, const char *what)
{
    failures += !c;
    printf("  %s: %s\n", c ? "ok" : "FAIL", what);
}

static bool broke_after(uint32_t w1, uint32_t w2, unsigned cause)
{
    retained[0] = w1;
    retained[1] = w2;
    reset_cause = cause;
    retained_start();
    return retained_nwp_broke();
}

int main(void)
{
    printf("P1 breakdown marker of the network processor's start\n");
    retained_progress(RETAINED_NWP_START);
    uint32_t w1 = retained[0], w2 = retained[1];
    check(broke_after(w1, w2, START_POWER_ON), "marker after a power-on start");
    check(broke_after(w1, w2, START_HIB_EXIT), "marker after a hibernation exit");
    check(!broke_after(w1, w2 & ~REC_VERSION, START_HIB_EXIT), "state record with the same first word: no marker");
    retained_progress(1);
    check(!broke_after(retained[0], retained[1], START_POWER_ON), "another progress value: no marker");
    printf("%d failure(s)\n", failures);
    return failures != 0;
}
