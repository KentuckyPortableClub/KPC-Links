#pragma once
#include <stddef.h>
#include <stdarg.h>
typedef struct FILE FILE; extern FILE* stderr; extern FILE* stdout;
int printf(const char* f, ...); int fprintf(FILE* f, const char* fmt, ...); int snprintf(char* b, size_t n, const char* f, ...); int sprintf(char* b, const char* f, ...);
