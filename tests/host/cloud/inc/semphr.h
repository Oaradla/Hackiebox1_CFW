#pragma once
#include "FreeRTOS.h"
typedef StaticQueue_t StaticSemaphore_t;
typedef QueueHandle_t SemaphoreHandle_t;
#define xSemaphoreCreateMutexStatic(m) ((SemaphoreHandle_t)(void *)(m))
#define xSemaphoreTake(s, t) ((void)(s), pdTRUE)
#define xSemaphoreGive(s) ((void)(s), pdTRUE)
