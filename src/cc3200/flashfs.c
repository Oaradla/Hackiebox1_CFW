/*
 * Flash files on the serial flash, through the network processor's file
 * system (SimpleLink).

 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#include <stddef.h>
#include "simplelink.h"
#include "FreeRTOS.h"
#include "task.h"
#include "flashfs.h"

/* Callers inside the file functions, and the hold that keeps new ones out
 * while the network processor stops. */
static volatile unsigned users;
static volatile bool held;

static void enter(void)
{
    for (;;)
    {
        taskENTER_CRITICAL();
        if (!held)
        {
            users++;
            taskEXIT_CRITICAL();
            return;
        }
        taskEXIT_CRITICAL();
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

static long leave(long r)
{
    taskENTER_CRITICAL();
    users--;
    taskEXIT_CRITICAL();
    return r;
}

void flashfs_hold(bool on)
{
    held = on;
}

bool flashfs_busy(void)
{
    return users != 0;
}

long flashfs_size(const char *name)
{
    SlFsFileInfo_t info;
    enter();
    long r = sl_FsGetInfo((unsigned char *)name, 0, &info);
    return leave(r < 0 ? r : (long)info.FileLen);
}

long flashfs_read(const char *name, uint32_t offset, void *buf, unsigned n)
{
    long fh;
    enter();
    long r = sl_FsOpen((unsigned char *)name, FS_MODE_OPEN_READ, NULL, &fh);
    if (r < 0)
    {
        return leave(r);
    }
    r = sl_FsRead(fh, offset, buf, n);
    sl_FsClose(fh, NULL, NULL, 0);
    return leave(r);
}

long flashfs_write(const char *name, const void *buf, unsigned n)
{
    long fh;
    enter();
    long r = sl_FsOpen((unsigned char *)name, FS_MODE_OPEN_WRITE, NULL, &fh);
    if (r < 0)
    {
        r = sl_FsOpen((unsigned char *)name, FS_MODE_OPEN_CREATE(n < 64 ? 64 : n, _FS_FILE_OPEN_FLAG_COMMIT), NULL,
                      &fh);
    }
    if (r < 0)
    {
        return leave(r);
    }
    r = sl_FsWrite(fh, 0, (unsigned char *)buf, n);
    long c = sl_FsClose(fh, NULL, NULL, 0);
    return leave(c < 0 ? c : r);
}

long flashfs_replace(const char *name, const void *buf, unsigned n, bool failsafe)
{
    long fh;
    enter();
    sl_FsDel((unsigned char *)name, 0);
    long r = sl_FsOpen((unsigned char *)name, FS_MODE_OPEN_CREATE(n, failsafe ? _FS_FILE_OPEN_FLAG_COMMIT : 0), NULL,
                       &fh);
    if (r >= 0)
    {
        r = sl_FsWrite(fh, 0, (unsigned char *)buf, n);
        long c = sl_FsClose(fh, NULL, NULL, 0);
        r = c < 0 ? c : r;
    }
    return leave(r);
}

long flashfs_delete(const char *name)
{
    enter();
    return leave(sl_FsDel((unsigned char *)name, 0));
}
