/*
 * Global resume: position reports to the teddyCloud server and the
 * server's answer to a position query.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#ifndef GRES_H
#define GRES_H

#include <stdbool.h>
#include <stdint.h>
#include "ext.h"

typedef enum
{
    GRES_STOPPED = 0,
    GRES_PLAYING = 1,
    GRES_ENDED = 2,
    GRES_LATE = 3,
    GRES_QUERY = 4
} gres_reason_t;

typedef enum
{
    GRES_NONE = -1, /* no answer yet */
    GRES_TAKE = 0,  /* the state holds the server's position */
    GRES_KEEP = 1,  /* the local position is the server's */
    GRES_CONFLICT = 2
} gres_answer_t;

/* The server takes reports: hello received and the log connection open. */
bool gres_online(void);

/* Position record of the figure in r (global: it has global resume);
 * nothing before the hello. */
void gres_report(const ext_state_t *r, bool global, gres_reason_t reason);

/* Sends the query for local (its UID set, the rest 0 without a state)
 * and waits for the answer of that UID from now on. */
void gres_query(const ext_state_t *local);

/* The answer, once it is in; *out holds the position for GRES_TAKE. */
gres_answer_t gres_answer(ext_state_t *out);

/* No answer is waited for any more; the answer that came in until then. */
gres_answer_t gres_cancel(ext_state_t *out);

/* Remote command 74; the result of the command. */
uint8_t gres_command(const uint8_t *arg, unsigned n);

/* After the hello: one of the positions stored while the server could not
 * be told, reported once the earlier records have been written to the log
 * connection, and marked as sent; true while some may still be due. */
bool gres_backlog(void);

#endif
