#pragma once
#include <stddef.h>
void* malloc(size_t n); void* calloc(size_t a, size_t b); void free(void* p); void* realloc(void* p, size_t n);
static inline int abs(int x) { return x < 0 ? -x : x; }
double atof(const char* s);
