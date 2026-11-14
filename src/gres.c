/*
 * Global resume (see gres.h).
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include "FreeRTOS.h"
#include "task.h"
#include "port.h"
#include "debug.h"
#include "ext.h"
#include "gres.h"
#include "player.h"
#include "rtnl.h"

static volatile int8_t answer = GRES_NONE;
static volatile bool waiting;
static ext_state_t wanted; /* UID asked for; the position of a GRES_TAKE */

static uint32_t le32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

bool gres_online(void)
{
    return ext_hello_received() && log_connected();
}

static void record(uint16_t function, const ext_state_t *r, bool global, gres_reason_t reason)
{
    log_args_t a = {0};
    log_arg_num(&a, (int32_t)le32(r->uid));
    log_arg_num(&a, (int32_t)le32(r->uid + 4));
    log_arg_num(&a, (int32_t)r->audio_id);
    log_arg_num(&a, (int32_t)r->position);
    log_arg_num(&a, (int32_t)r->seed);
    log_arg_num(&a, (int32_t)(r->index | (uint32_t)r->chapters << 8 |
                              (uint32_t)(r->flags & EXT_STATE_SHUFFLING) << 16 | (uint32_t)global << 17));
    log_arg_num(&a, reason);
    log_arg_num(&a, global ? (int32_t)(r->base | (uint32_t)r->listened << 16) : 0);
    log_fn(LOG_INFO, 22, function, 0, &a);
}

void gres_report(const ext_state_t *r, bool global, gres_reason_t reason)
{
    if (ext_hello_received())
    {
        record(32263, r, global, reason);
    }
}

void gres_query(const ext_state_t *local)
{
    CRITICAL_ENTER();
    memset(&wanted, 0, sizeof wanted);
    memcpy(wanted.uid, local->uid, 8);
    answer = GRES_NONE;
    waiting = true;
    CRITICAL_EXIT();
    record(32264, local, true, GRES_QUERY);
}

gres_answer_t gres_answer(ext_state_t *out)
{
    CRITICAL_ENTER();
    gres_answer_t a = (gres_answer_t)answer;
    if (a == GRES_TAKE)
    {
        *out = wanted;
    }
    CRITICAL_EXIT();
    return a;
}

gres_answer_t gres_cancel(ext_state_t *out)
{
    waiting = false;
    return gres_answer(out);
}

uint8_t gres_command(const uint8_t *arg, unsigned n)
{
    if (n < 9 || arg[8] > 2 || (arg[8] == GRES_TAKE ? n != 26 : n != 9))
    {
        return PLAYER_RC_ARGS;
    }
    uint8_t rc = PLAYER_RC_STATE;
    CRITICAL_ENTER();
    if (waiting && answer == GRES_NONE && !memcmp(arg, wanted.uid, 8))
    {
        if (arg[8] == GRES_TAKE)
        {
            wanted.base = (uint16_t)(arg[9] | arg[10] << 8);
            wanted.audio_id = le32(arg + 11);
            wanted.position = le32(arg + 15);
            wanted.seed = le32(arg + 19);
            wanted.index = arg[23];
            wanted.chapters = arg[24];
            wanted.flags = arg[25] & EXT_STATE_SHUFFLING;
            wanted.listened = 0;
        }
        answer = (int8_t)arg[8];
        waiting = false;
        rc = PLAYER_RC_DONE;
    }
    CRITICAL_EXIT();
    return rc;
}

/* Sequences of the records reported during a playback, not marked yet;
 * none while sent_high is 0. */
static uint32_t sent_low, sent_high;

bool gres_backlog(bool playing)
{
    ext_state_t r;
    if (!gres_online() || !log_sent())
    {
        return true;
    }
    r.sequence = playing && sent_high ? sent_low : 0xFFFFFFFFu;
    if (!ext_state_get(NULL, &r))
    {
        sent_high = playing ? sent_high : 0;
        return false;
    }
    if (!sent_high || r.sequence < sent_low || r.sequence > sent_high)
    {
        record(32263, &r, true, GRES_LATE);
    }
    if (playing)
    {
        sent_high = sent_high ? sent_high : r.sequence;
        sent_low = r.sequence;
        return true;
    }
    r.flags &= (uint8_t)~EXT_STATE_UNREPORTED;
    if (!ext_state_put(&r))
    {
        debug_printf("pl: state file not written\n");
        return false;
    }
    return true;
}
