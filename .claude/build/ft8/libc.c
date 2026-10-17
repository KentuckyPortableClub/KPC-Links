#include <stddef.h>
#include <stdint.h>
#include <stdarg.h>
#include "inc/stdio.h"
/* tiny heap: bump allocator (the FT8 code only allocates when it starts) + memory.grow */
extern unsigned char __heap_base;
static uintptr_t heap = 0, heap_end = 0;
void* malloc(size_t n) {
  if (!heap) { heap = (uintptr_t)&__heap_base; heap_end = __builtin_wasm_memory_size(0) * 65536; }
  heap = (heap + 15) & ~(uintptr_t)15; uintptr_t p = heap; heap += n + 16;
  while (heap > heap_end) { if (__builtin_wasm_memory_grow(0, 16) == (size_t)-1) return 0; heap_end += 16 * 65536; }
  *(size_t*)p = n; return (void*)(p + 16);
}
void free(void* p) { (void)p; }
void* memset(void* d, int c, size_t n) { unsigned char* x = d; while (n--) *x++ = (unsigned char)c; return d; }
void* memcpy(void* d, const void* s, size_t n) { unsigned char* a = d; const unsigned char* b = s; while (n--) *a++ = *b++; return d; }
void* memmove(void* d, const void* s, size_t n) { unsigned char* a = d; const unsigned char* b = s; if (a < b) while (n--) *a++ = *b++; else { a += n; b += n; while (n--) *--a = *--b; } return d; }
void* calloc(size_t a, size_t b) { void* p = malloc(a * b); if (p) memset(p, 0, a * b); return p; }
void* realloc(void* p, size_t n) { void* q = malloc(n); if (p && q) { size_t o = *(size_t*)((char*)p - 16); memcpy(q, p, o < n ? o : n); } return q; }
int memcmp(const void* a, const void* b, size_t n) { const unsigned char *x = a, *y = b; for (; n; n--, x++, y++) if (*x != *y) return *x - *y; return 0; }
size_t strlen(const char* s) { size_t n = 0; while (s[n]) n++; return n; }
char* strcpy(char* d, const char* s) { char* r = d; while ((*d++ = *s++)); return r; }
char* strncpy(char* d, const char* s, size_t n) { size_t i = 0; for (; i < n && s[i]; i++) d[i] = s[i]; for (; i < n; i++) d[i] = 0; return d; }
int strcmp(const char* a, const char* b) { while (*a && *a == *b) a++, b++; return (unsigned char)*a - (unsigned char)*b; }
int strncmp(const char* a, const char* b, size_t n) { for (; n; n--, a++, b++) { if (*a != *b || !*a) return (unsigned char)*a - (unsigned char)*b; } return 0; }
char* strchr(const char* s, int c) { for (;; s++) { if (*s == (char)c) return (char*)s; if (!*s) return 0; } }
char* strcat(char* d, const char* s) { strcpy(d + strlen(d), s); return d; }
char* strncat(char* d, const char* s, size_t n) { char* e = d + strlen(d); while (n-- && *s) *e++ = *s++; *e = 0; return d; }
char* strstr(const char* h, const char* n) { size_t k = strlen(n); if (!k) return (char*)h; for (; *h; h++) if (!strncmp(h, n, k)) return (char*)h; return 0; }
FILE* stderr = 0; FILE* stdout = 0;
int printf(const char* f, ...) { (void)f; return 0; } int fprintf(FILE* x, const char* f, ...) { (void)x; (void)f; return 0; }
int sprintf(char* b, const char* f, ...) { (void)f; b[0] = 0; return 0; } int snprintf(char* b, size_t n, const char* f, ...) { (void)f; if (n) b[0] = 0; return 0; }
double atof(const char* s) { (void)s; return 0; }
/* erf (Abramowitz & Stegun 7.1.26 is too rough; use a series / continued fraction good to ~1e-7) */
float expf(float); float erff(float x) { float s = x < 0 ? -1 : 1; x = x < 0 ? -x : x; if (x > 4) return s;
  double t = 1.0 / (1.0 + 0.5 * x), y = 1 - t * expf((float)(-x * x - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 + t * (-0.18628806 + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (-0.82215223 + t * 0.17087277)))))))))); return (float)(s * y); }
int atoi(const char* s){int n=0,g=1;while(*s==' ')s++;if(*s=='-'){g=-1;s++;}else if(*s=='+')s++;while(*s>='0'&&*s<='9'){n=n*10+(*s-'0');s++;}return n*g;}
char* stpcpy(char* d,const char* s){while((*d=*s)){d++;s++;}return d;}
void exit(int c){__builtin_trap();}
