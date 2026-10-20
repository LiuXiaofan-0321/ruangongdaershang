#ifndef THREADS_FIXED_POINT_H
#define THREADS_FIXED_POINT_H

#include <stdint.h>

/* 17.14 定点数：低 14 位是小数部分，高 17 位是整数部分（含符号位）。
   内核里不能用浮点（CFLAGS 带 -msoft-float，且中断里也不保存 FPU 状态），
   所以 MLFQS 中的 load_avg、recent_cpu 都用这种整数模拟的小数来算。 */
typedef int fixed_t;

#define FP_SHIFT 14
#define FP_F (1 << FP_SHIFT)

/* 整数 n 转成定点数。 */
#define INT_TO_FP(n) ((fixed_t) ((n) * FP_F))
/* 定点数 x 转整数，向 0 取整。 */
#define FP_TO_INT_ZERO(x) ((x) / FP_F)
/* 定点数 x 转整数，四舍五入。 */
#define FP_TO_INT_NEAREST(x) ((x) >= 0 ? ((x) + FP_F / 2) / FP_F \
                                       : ((x) - FP_F / 2) / FP_F)

/* 定点数与定点数之间的加减。 */
#define FP_ADD(x, y) ((x) + (y))
#define FP_SUB(x, y) ((x) - (y))
/* 定点数与整数之间的加减。 */
#define FP_ADD_INT(x, n) ((x) + (n) * FP_F)
#define FP_SUB_INT(x, n) ((x) - (n) * FP_F)
/* 定点数乘除：中间结果先扩成 64 位，否则 x * y 很容易溢出。 */
#define FP_MUL(x, y) ((fixed_t) (((int64_t) (x)) * (y) / FP_F))
#define FP_DIV(x, y) ((fixed_t) (((int64_t) (x)) * FP_F / (y)))
/* 定点数与整数之间的乘除，不会溢出，直接算。 */
#define FP_MUL_INT(x, n) ((x) * (n))
#define FP_DIV_INT(x, n) ((x) / (n))

#endif /* threads/fixed-point.h */
