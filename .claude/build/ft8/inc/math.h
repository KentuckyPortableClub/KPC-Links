#pragma once
#define M_PI 3.14159265358979323846
#define INFINITY (__builtin_inff())
#define NAN (__builtin_nanf(""))
float sinf(float); float cosf(float); float expf(float); float logf(float); float log10f(float); float powf(float, float); float atan2f(float, float); float fmodf(float, float); float erff(float);
double sin(double); double cos(double); double exp(double); double log(double); double log10(double); double pow(double, double); double atan2(double, double); double fmod(double, double);
static inline float sqrtf(float x) { return __builtin_sqrtf(x); } static inline double sqrt(double x) { return __builtin_sqrt(x); }
static inline float fabsf(float x) { return __builtin_fabsf(x); } static inline double fabs(double x) { return __builtin_fabs(x); }
static inline float floorf(float x) { return __builtin_floorf(x); } static inline double floor(double x) { return __builtin_floor(x); }
static inline float ceilf(float x) { return __builtin_ceilf(x); } static inline double ceil(double x) { return __builtin_ceil(x); }
static inline float roundf(float x) { return __builtin_roundf(x); } static inline float truncf(float x) { return __builtin_truncf(x); }
static inline long lroundf(float x) { return (long)__builtin_roundf(x); }
