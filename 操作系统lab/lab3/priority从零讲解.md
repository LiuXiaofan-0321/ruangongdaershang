# 从零讲清楚 Pintos 的 priority-*

> 这份稿子是给自己准备上台（作业 3.2）用的：从“Pintos 的线程到底是怎么跑起来的”讲起，一直讲到 12 个 priority 测试是怎么一个个通过的。读完应该能做到：PPT 上每一页都能脱稿讲，老师追问任何一行代码都能说出“为什么这么写、不这么写会挂哪个测试”。
>
> 建议读法：第 1～3 节是基础，先看懂；第 4～8 节是实现，对照 `修改后的源文件/src/threads/` 里的代码看；第 9 节是三个最难测试的逐步推演，最好自己在纸上跟着画一遍；第 10～11 节是上台前的冲刺材料。

---

## 目录

1. Pintos 的线程是怎么跑起来的
2. 原始代码为什么“不认优先级”
3. 同步原语：信号量、锁、条件变量
4. 我们要过的 12 个测试，各自在问什么
5. 第一步：就绪队列按优先级排序
6. 第二步：抢占——什么时候必须马上让出 CPU
7. 第三步：信号量和条件变量按优先级唤醒
8. 第四步：优先级捐赠（重点）
9. 三个最难测试的逐步推演
10. 我踩过的坑（对应 PPT）
11. 上台讲解要点 + 问答准备
12. 名词速查

---

## 1. Pintos 的线程是怎么跑起来的

### 1.1 一个线程 = 一页内存

Pintos 里每个线程占 4 KB 的一页：页的底部放 `struct thread`，上面剩下的空间是这个线程的内核栈（从顶往下长）。所以 `thread_current()` 的实现很巧妙：把当前栈指针 `esp` 向下取整到页边界，就是当前线程的 `struct thread`。

`struct thread` 里和本次实验相关的字段（带 ★ 的是我加的）：

```c
struct thread {
  tid_t tid;
  enum thread_status status;   /* RUNNING / READY / BLOCKED / DYING */
  char name[16];
  int priority;                /* 实际优先级（捐赠后的） */
  struct list_elem elem;       /* 挂在 ready_list 或某个 waiters 上 */
  ...
  int base_priority;           /* ★ 自己设置的原始优先级 */
  struct list locks;           /* ★ 当前持有的锁 */
  struct lock *waiting_lock;   /* ★ 正在等待的锁 */
};
```

优先级范围是 `PRI_MIN = 0` 到 `PRI_MAX = 63`，**数字越大越优先**，默认 `PRI_DEFAULT = 31`。

### 1.2 线程的四种状态

```
             thread_create
                  │
                  ▼
   ┌──────────► READY ──────────┐
   │   thread_unblock     schedule() 选中
   │                            ▼
BLOCKED ◄──── thread_block ── RUNNING ──── thread_exit ──► DYING
                                │  ▲
                                └──┘
                          thread_yield（回到 READY）
```

- **RUNNING**：正在 CPU 上跑，任何时刻只有一个（Pintos 是单核）。
- **READY**：可以跑，但 CPU 被别人占着，排在 `ready_list` 里。
- **BLOCKED**：在等某件事（等信号量、等锁、睡眠），不在 `ready_list` 里。
- **DYING**：结束了，等下一个线程把它的页释放掉。

### 1.3 调度器：谁下一个上 CPU？

所有“换人”最终都走到 `schedule()`：

```c
static void
schedule (void) 
{
  struct thread *cur = running_thread ();
  struct thread *next = next_thread_to_run ();   /* 选下一个 */
  ...
  if (cur != next)
    prev = switch_threads (cur, next);           /* 真正切换寄存器和栈 */
  thread_schedule_tail (prev);
}
```

`next_thread_to_run()` 原来就是“从 `ready_list` 队首拿一个，队列空就跑 idle 线程”。**这个函数我一行没改**——我改的是“往 `ready_list` 里放的时候按什么顺序放”。

会调用 `schedule()` 的三个入口：

| 函数 | 当前线程变成 | 典型场景 |
|---|---|---|
| `thread_yield()` | READY（重新排队） | 主动让出、时间片用完 |
| `thread_block()` | BLOCKED | `sema_down` 等不到、`timer_sleep` |
| `thread_exit()` | DYING | 线程函数返回 |

### 1.4 时钟中断和时间片

硬件定时器每秒中断 100 次（`TIMER_FREQ = 100`），每次叫一个 tick。中断处理函数 `timer_interrupt` 调用 `thread_tick()`，里面数一下当前线程连续跑了几个 tick，满 4 个（`TIME_SLICE = 4`）就要求换人：

```c
  if (++thread_ticks >= TIME_SLICE)
    intr_yield_on_return ();
```

注意这里**不是** `thread_yield()`，而是 `intr_yield_on_return()`。这一点后面非常关键（我就是在这里栽的跟头，见第 10 节）。

### 1.5 中断上下文 vs 线程上下文

- **线程上下文**：普通代码，属于某个线程，可以睡眠、可以切换线程。
- **中断上下文**：正在处理中断（比如 `timer_interrupt`）。这时 CPU 只是“临时借用”被打断线程的栈，**不能睡眠、不能切换线程**。`intr_context()` 返回 true 就说明在中断里。

所以 `thread_yield()` 第一行就是 `ASSERT (!intr_context ());`。在中断里想换人，只能用 `intr_yield_on_return()`：设一个标记，等中断处理完、返回之前再调 `thread_yield()`。

### 1.6 关中断 = 原子操作

Pintos 是单核的，只要把中断关掉（`intr_disable()`），就不会有时钟中断来抢占，当前这段代码就不会被打断。所以内核里改共享数据结构（`ready_list`、`waiters`、优先级）时的标准写法是：

```c
enum intr_level old_level = intr_disable ();
/* ……修改共享数据…… */
intr_set_level (old_level);   /* 恢复成原来的状态，而不是无脑开中断 */
```

我在 `lock_acquire`、`lock_release`、`thread_set_priority` 里都是这么做的。

### 1.7 Pintos 的链表（理解后面代码必须看）

Pintos 的 `list` 是“侵入式”链表：链表节点 `struct list_elem` 是**嵌在** `struct thread` 里面的（就是那个 `elem` 字段），而不是链表节点里存一个指向线程的指针。从节点找回线程用宏：

```c
struct thread *t = list_entry (e, struct thread, elem);
```

本次用到的几个链表函数：

| 函数 | 作用 |
|---|---|
| `list_push_back(list, e)` | 插到队尾 |
| `list_pop_front(list)` | 取出队首 |
| `list_insert_ordered(list, e, less, aux)` | 找到**第一个**满足 `less(e, x)` 的元素 x，插在 x 前面 |
| `list_min(list, less, aux)` | 返回最小元素；有多个时返回**最前面**那个 |
| `list_max(list, less, aux)` | 返回最大元素；有多个时返回**最前面**那个 |
| `list_remove(e)` | 把 e 从它所在的链表里摘掉 |

还有一个细节：**`elem` 只有一个**，所以一个线程同一时刻只能挂在一个链表上。READY 的线程挂在 `ready_list` 上；BLOCKED 的线程挂在某个信号量的 `waiters` 上（或者 `sleep_list` 上）。这两种状态互斥，所以够用。（`allelem` 是另一个字段，用来挂所有线程的 `all_list`。）

---

## 2. 原始代码为什么“不认优先级”

原始代码里：

```c
/* thread_unblock 和 thread_yield 里 */
list_push_back (&ready_list, &t->elem);      /* 插到队尾 */

/* next_thread_to_run 里 */
list_pop_front (&ready_list);                /* 从队首取 */
```

队尾进、队首出，就是普通的**先来先服务轮转（round-robin）**。`priority` 字段虽然存在，`thread_create` 也会设置它，但调度的时候根本没人看它。同样，`sema_up` 唤醒等待者也是 `list_pop_front`，谁先来叫谁，跟优先级无关。

所以要做的事情归结为三句话（也是课件第 10 页的三点）：

1. **选谁跑**：从就绪队列选优先级最高的。
2. **抢占**：新来的（或刚被唤醒的、优先级刚变的）线程如果比当前线程高，当前线程要马上让出 CPU。
3. **同步原语**：信号量、锁、条件变量唤醒等待者时，选优先级最高的；锁还要解决优先级反转（捐赠）。

---

## 3. 同步原语：信号量、锁、条件变量

### 3.1 信号量 semaphore

一个非负整数 `value` + 一个等待队列 `waiters`：

- `sema_down`（P 操作）：`value` 为 0 就把自己挂到 `waiters` 上并 `thread_block()`；等醒来后 `value--`。
- `sema_up`（V 操作）：如果 `waiters` 不空就叫醒一个（`thread_unblock`），然后 `value++`。

`sema_up` 可以在中断里调用（它不会睡眠），这一点决定了我在 `thread_preempt()` 里要判断 `intr_context()`。

### 3.2 锁 lock

锁 = 初值为 1 的信号量 + 一个 `holder` 字段（记录谁拿着它）。区别：信号量谁都能 up；锁只能由持有者释放，而且同一把锁同一时刻只有一个持有者。

**正是因为锁有“持有者”，才能做优先级捐赠**：我知道是谁挡住了我，就可以把优先级借给它。信号量没有持有者，所以 Pintos 只要求对锁做捐赠。

### 3.3 条件变量 condition

`cond_wait(cond, lock)`：释放锁、睡下去等信号、醒来后重新拿锁。`cond_signal`：叫醒一个在等的线程。Pintos 的实现很巧：每个等待者在自己的栈上建一个只属于自己的信号量（`struct semaphore_elem`），挂到 `cond->waiters` 上，然后在这个私人信号量上 `sema_down`；`cond_signal` 就是从 `cond->waiters` 里挑一个，对它的私人信号量 `sema_up`。

所以 `cond->waiters` 里放的不是线程，而是 `semaphore_elem`——这就是为什么改 `cond_signal` 时需要在 `semaphore_elem` 里多存一个线程指针。

Pintos 的条件变量是 **Mesa 风格**：signal 之后被唤醒的线程不是立刻运行，而是要重新竞争锁，所以使用者一般要用 `while` 重新检查条件。

---

## 4. 我们要过的 12 个测试，各自在问什么

测试源码在 `src/tests/threads/priority-*.c`，期望输出在同名的 `.ck` 文件里。我的方法是先把它们全读一遍再动手。

### 第一类：调度与抢占

| 测试 | 场景 | 在问什么 |
|---|---|---|
| **priority-change** | 主线程(31)创建 thread 2(32)；thread 2 把自己降到 30；主线程再把自己降到 29 | 创建了更高优先级的线程要马上让它跑；**自己降低优先级后**如果别人更高，也要马上让出 |
| **priority-preempt** | 主线程(31)创建一个 32 的线程，它循环 5 次 `thread_yield` | 高优先级线程必须在 `thread_create` 返回**之前**就跑完 |
| **priority-fifo** | 主线程先升到 33，创建 16 个优先级都是 32 的线程，再降回 31；每个线程循环 16 次“拿锁→记下自己的编号→放锁→yield” | **同优先级之间必须轮转**，16 轮的顺序完全一样 |

### 第二类：按优先级唤醒

| 测试 | 场景 | 在问什么 |
|---|---|---|
| **priority-sema** | 10 个优先级 21～30（乱序创建）的线程在同一个信号量上 `sema_down`；主线程(PRI_MIN)`sema_up` 10 次 | 每次 `sema_up` 都要叫醒剩下的里面优先级最高的，并且立刻让它运行 |
| **priority-condvar** | 10 个线程在同一个条件变量上 `cond_wait`；主线程 `cond_signal` 10 次 | 同上，换成条件变量 |

### 第三类：优先级捐赠

| 测试 | 场景 | 在问什么 |
|---|---|---|
| **donate-one** | 主线程(31)拿着锁；32、33 先后来等 | 最基本的捐赠；放锁后 33 先拿到锁 |
| **donate-multiple** | 主线程拿着 a、b 两把锁；32 等 a，33 等 b；先放 b 再放 a | **多重捐赠**：放 b 后应该回到 32（a 上的捐赠还在），而不是 31 |
| **donate-multiple2** | 同上，但 34 等 a，36 等 b，中间还有一个不等锁的 c(32)；先放 a 再放 b | 放 a 后仍是 36；全放完后运行顺序是 b、a、c |
| **donate-nest** | L(31) 拿 a；M(32) 拿 b 再等 a；H(33) 等 b | **嵌套捐赠**：H→M→L，L 要变成 33 |
| **donate-chain** | 7 层锁链，主线程(0)在最底下；每层还有一个比捐赠者低 1 的 interloper | 嵌套捐赠一路传到底；释放时逐层收回，interloper 不能插队 |
| **donate-sema** | L(32) 拿锁后在信号量上等，M(34) 也在这个信号量上等，H(36) 等 L 的锁 | 等待队列里的线程被捐赠后，`sema_up` 还能挑对人 |
| **donate-lower** | 主线程被捐赠到 41 后，把自己的优先级设成 21 | 被捐赠期间改优先级，只改“原始优先级”，实际仍是 41 |

---

## 5. 第一步：就绪队列按优先级排序

### 5.1 怎么改

把放进 `ready_list` 的两处（`thread_unblock` 和 `thread_yield`）从 `list_push_back` 改成按优先级降序插入：

```c
list_insert_ordered (&ready_list, &t->elem, thread_priority_more, NULL);
```

比较函数：

```c
bool
thread_priority_more (const struct list_elem *a, const struct list_elem *b,
                      void *aux UNUSED)
{
  return list_entry (a, struct thread, elem)->priority
         > list_entry (b, struct thread, elem)->priority;
}
```

这样 `ready_list` 永远是从高到低排好的，`next_thread_to_run()` 照旧取队首，取到的就是最高优先级的线程。

### 5.2 为什么必须是 `>` 而不是 `>=`（priority-fifo）

回忆 `list_insert_ordered`：找到**第一个**满足 `less(新元素, x)` 的 x，插在 x 前面。

假设队列里已经有三个优先级 32 的线程 `[#1 32] [#2 32] [#3 32]`，现在 #0（也是 32）`thread_yield` 重新入队：

- 用 `>`：`32 > 32` 为假，一直找不到，插到所有 32 的**后面** → `[#1][#2][#3][#0]`，大家轮流来，**FIFO**。
- 用 `>=`：`32 >= 32` 为真，第一个就满足，插到 #1 **前面** → `[#0][#1][#2][#3]`，下一次又选中 #0 自己，`thread_yield` 等于没让。

用 `>=` 时 priority-fifo 的输出是这样的（我真跑出来过）：

```text
(priority-fifo) iteration: 15 15 15 15 15 15 15 15 15 15 15 15 15 15 15 15
(priority-fifo) iteration: 14 14 14 14 14 14 14 14 14 14 14 14 14 14 14 14
...
```

同一个线程连跑 16 次。而 alarm-priority、priority-sema 里每个线程优先级都不同，这个 bug 在它们那里完全看不出来。

---

## 6. 第二步：抢占——什么时候必须马上让出 CPU

### 6.1 thread_preempt

光排好序还不够：排序只决定“**下次**换人时选谁”，可如果当前线程一直不让出 CPU，高优先级线程就只能等到时间片用完（最多 4 个 tick）。测试要求的是**立刻**。所以写了一个公共函数：

```c
/* 如果就绪队列里有比当前线程优先级更高的线程，就让出 CPU。 */
void
thread_preempt (void)
{
  enum intr_level old_level = intr_disable ();

  if (!list_empty (&ready_list)
      && list_entry (list_front (&ready_list), struct thread, elem)->priority
         > thread_current ()->priority)
    {
      if (intr_context ())
        intr_yield_on_return ();   /* 中断里不能直接切换 */
      else
        thread_yield ();
    }
  intr_set_level (old_level);
}
```

因为 `ready_list` 有序，只要看队首就够了。

### 6.2 在哪里调用

原则：**任何可能让“就绪队列里出现比我更高的线程”的地方**。

| 位置 | 为什么 | 对应测试 |
|---|---|---|
| `thread_create()` 末尾 | 新线程可能比我高 | priority-preempt、priority-change、donate-one |
| `thread_set_priority()` 末尾 | 我降低了自己的优先级 | priority-change |
| `sema_up()` 末尾 | 被叫醒的线程可能比我高 | priority-sema、所有锁相关测试（`lock_release` 内部调用 `sema_up`） |
| `thread_wake()`（时钟中断里） | 睡醒的线程可能比当前线程高 | alarm-priority 的语义 |

`thread_wake` 在中断里，所以那里直接用 `intr_yield_on_return()`。

### 6.3 如果 thread_create 后不抢占会怎样

priority-preempt 会输出这样的东西（也是我真跑过的）：

```text
(priority-preempt) (priority-preempt) Thread high-priority iteration 0
...
The high-priority thread should have already completed.
```

主线程没让出 CPU，接着去打印 “The high-priority thread should have already completed.”，刚打印了前缀 `(priority-preempt) ` 就被时钟中断打断（时间片到了），高优先级线程这才上 CPU，于是两行输出搅在了一起。

---

## 7. 第三步：信号量和条件变量按优先级唤醒

### 7.1 sema_down / sema_up

`sema_down` 里排队时按优先级有序插入（和 `ready_list` 一样）。但**只在插入时排序是不够的**：线程在等待期间，优先级可能因为捐赠而变化，插入时排好的顺序就失效了（donate-sema 就是这种情况，第 9.3 节详细推演）。所以 `sema_up` 时重新找一次最高的：

```c
void
sema_up (struct semaphore *sema) 
{
  enum intr_level old_level;

  old_level = intr_disable ();
  if (!list_empty (&sema->waiters)) 
    {
      struct list_elem *e = list_min (&sema->waiters,
                                      thread_priority_more, NULL);
      list_remove (e);
      thread_unblock (list_entry (e, struct thread, elem));
    }
  sema->value++;
  thread_preempt ();          /* 叫醒的线程可能比我高 */
  intr_set_level (old_level);
}
```

**为什么是 `list_min` 配“大于”？** `list_min(list, less)` 返回“没有谁比它更 less”的第一个元素。我传进去的 `less` 其实是“优先级更高”，所以“最 less 的”就是**优先级最高的**；有多个时返回最前面的那个，也就是最早来的，同优先级仍然 FIFO。也可以写一个“小于”比较函数配 `list_max`，效果一样，我只是想少写一个函数。

### 7.2 cond_signal

`cond->waiters` 里是 `semaphore_elem`，我在里面加了线程指针：

```c
struct semaphore_elem 
  {
    struct list_elem elem;
    struct semaphore semaphore;
    struct thread *thread;              /* ★ 在这个信号量上等待的线程 */
  };
```

`cond_wait` 里记下 `waiter.thread = thread_current ();`，`cond_signal` 用 `list_max` 挑出线程优先级最高的那个：

```c
  if (!list_empty (&cond->waiters)) 
    {
      struct list_elem *e = list_max (&cond->waiters,
                                      sema_elem_priority_less, NULL);
      list_remove (e);
      sema_up (&list_entry (e, struct semaphore_elem, elem)->semaphore);
    }
```

**为什么不直接看每个私人信号量 `waiters` 的队首？** 因为 `cond_wait` 是先 `lock_release` 再 `sema_down` 的，中间可能被抢占。`cond_signal` 的时候，某个等待者可能还没来得及 `sema_down`，它的私人信号量等待队列是空的，取队首就出错了。直接存线程指针最稳。

---

## 8. 第四步：优先级捐赠（重点）

### 8.1 什么是优先级反转

```
时间 ───────────────────────────────────────────►
H  :      [跑]─请求锁─>[阻塞 ······················][拿到锁]
M  :              [一直在跑 ···················]
L  : [拿锁]                                     [放锁]
```

L 拿着锁 → H 来要锁，只能阻塞 → M 比 L 高，一直抢占 L → L 放不了锁 → H 一直等。**高优先级的 H 实际上被中优先级的 M 卡住了**，这就是优先级反转。1997 年火星探路者号反复重启就是这个原因（课件第 16～21 页）。

**解决：优先级捐赠（继承）**。H 等 L 的锁时，把自己的优先级“借”给 L。L 变成和 H 一样高，M 就抢不了它了；L 尽快跑完临界区放锁，放锁时把借来的优先级还回去，H 立刻拿到锁运行。

```
H  :      [跑]─请求锁─>[等]        [拿到锁 ···]
M  :                                         [M 之后再跑 ···]
L  : [拿锁]             [借 H 的优先级跑][放锁]
```

### 8.2 要处理的三种情况

1. **单一捐赠**（donate-one）：一个线程等一把锁。
2. **多重捐赠**（donate-multiple、multiple2）：一个线程拿着好几把锁，每把锁上都有人等。它的优先级应该是这些捐赠里**最高的**；放掉其中一把锁时，**只收回这把锁带来的捐赠**。
3. **嵌套捐赠**（donate-nest、chain）：H 等 M 的锁，M 又在等 L 的锁。H 的优先级要沿着链一路传到 L，否则 L 还是会被别人抢占，M 拿不到锁，H 也就拿不到。

### 8.3 数据结构设计：按“锁”记账

课件（第 22 页）建议给线程维护一个“捐赠者线程列表”。我想了一下：**捐赠总是按锁收回的**——放掉哪把锁，就收回因为这把锁得到的捐赠。所以换了一个记法：

- 线程记录自己**持有哪些锁**：`struct list locks`
- 每把锁记录**正在等它的线程里最高的优先级**：`int max_priority`
- 线程记录自己**正在等哪把锁**：`struct lock *waiting_lock`（用于沿链嵌套捐赠）
- 线程记录自己的**原始优先级**：`int base_priority`

```c
struct lock 
  {
    struct thread *holder;
    struct semaphore semaphore;
    struct list_elem elem;      /* ★ 挂在 holder->locks 上 */
    int max_priority;           /* ★ 等这把锁的线程中的最高优先级 */
  };
```

这样实际优先级只有一个公式：

> **priority = max(base_priority, 我持有的每把锁的 max_priority)**

例：main 自己是 31，拿着 a、b 两把锁，a 上有 32 在等，b 上有 33 在等 → `max(31, 32, 33) = 33`。放掉 b → `max(31, 32) = 32`。全放掉 → 31。

### 8.4 thread_update_priority：唯一的“算优先级”的地方

```c
void
thread_update_priority (struct thread *t)
{
  int priority = t->base_priority;
  struct list_elem *e;

  ASSERT (intr_get_level () == INTR_OFF);

  if (thread_mlfqs)
    return;

  for (e = list_begin (&t->locks); e != list_end (&t->locks);
       e = list_next (e))
    {
      struct lock *l = list_entry (e, struct lock, elem);
      if (l->max_priority > priority)
        priority = l->max_priority;
    }
  t->priority = priority;

  /* 如果 T 在就绪队列里，优先级变了，位置也要跟着变 */
  if (t->status == THREAD_READY)
    {
      list_remove (&t->elem);
      list_insert_ordered (&ready_list, &t->elem, thread_priority_more, NULL);
    }
}
```

最后那段很容易漏：被捐赠的线程如果正处于 READY，它在 `ready_list` 里的位置是按旧优先级排的，必须挪一下，不然调度器还是选不到它。

**设计的好处：** 等锁、放锁、改 base，都只调用这一个函数按公式重算，从来不在各处“加一点、减一点”。多重捐赠、嵌套捐赠、捐赠期间改优先级，这几种情况都不用写特判。

### 8.5 lock_acquire：捐出去

```c
void
lock_acquire (struct lock *lock)
{
  struct thread *cur = thread_current ();
  enum intr_level old_level;
  ...
  old_level = intr_disable ();

  if (!thread_mlfqs && lock->holder != NULL)
    {
      /* 锁被占用：记下自己在等哪把锁，然后沿着“锁 -> 持有者 ->
         持有者在等的锁 -> ...”这条链把优先级一路捐上去。 */
      struct lock *l = lock;
      int depth = 0;

      cur->waiting_lock = lock;
      while (l != NULL && l->holder != NULL && depth < DONATE_DEPTH_MAX
             && l->max_priority < cur->priority)
        {
          l->max_priority = cur->priority;     /* 捐给这把锁 */
          thread_update_priority (l->holder);  /* 持有者按公式重算 */
          l = l->holder->waiting_lock;         /* 顺着链往下一层 */
          depth++;
        }
    }

  sema_down (&lock->semaphore);   /* 真正等锁（可能阻塞） */

  /* 拿到锁了 */
  cur->waiting_lock = NULL;
  lock->holder = cur;
  if (!thread_mlfqs)
    {
      /* 还在等这把锁的线程，现在要转而向我捐赠 */
      lock->max_priority = PRI_MIN;
      if (!list_empty (&lock->semaphore.waiters))
        lock->max_priority = list_entry (list_min (&lock->semaphore.waiters,
                                                   thread_priority_more, NULL),
                                         struct thread, elem)->priority;
      list_push_back (&cur->locks, &lock->elem);
      thread_update_priority (cur);
    }
  intr_set_level (old_level);
}
```

逐段解释：

1. **为什么整个函数关中断？** 捐赠要同时改好几个线程和锁的状态，中途被打断的话别的线程会看到“改了一半”的数据。
2. **循环的四个停止条件：**
   - `l == NULL`：链到头了，最后一个持有者没有在等别的锁。
   - `l->holder == NULL`：锁刚被释放、新持有者还没设上（见下面“隐患”）。
   - `depth >= 8`：防止锁链太长或出现环时死循环。Pintos 文档允许设一个合理的深度上限（比如 8 层）；donate-chain 正好 7 层，够用。
   - `l->max_priority >= cur->priority`：这把锁上已经有同样高或更高的捐赠了，往下也不用再捐。
3. **为什么拿到锁后要重算 `lock->max_priority`？** 这把锁上可能还有别的线程在等，它们原来是捐给前一个持有者的；现在我是持有者，它们应该转而捐给我。前一个持有者在 `lock_release` 时已经把这把锁从自己的 `locks` 里删了，不会再受它影响。
4. **隐患（`l->holder != NULL` 的由来）：** A 刚 `lock_release`，把 `holder` 置成 NULL 并叫醒了等待者 B，但 B 还没被调度、没来得及把自己设成 `holder`，这时 B 的 `waiting_lock` 仍然指着这把锁。如果此时有另一个线程沿链捐赠到 B，再往下一步就会访问 `NULL->waiting_lock`。测试里没触发，但加上这个判断更安全。

### 8.6 lock_release：收回来

```c
void
lock_release (struct lock *lock) 
{
  enum intr_level old_level;
  ...
  old_level = intr_disable ();
  if (!thread_mlfqs)
    {
      list_remove (&lock->elem);                 /* 这把锁不再算我的 */
      thread_update_priority (thread_current ()); /* 按剩下的锁重算 */
    }
  lock->holder = NULL;
  sema_up (&lock->semaphore);   /* 叫醒等待者；末尾 thread_preempt 负责让出 CPU */
  intr_set_level (old_level);
}
```

只有两件事：把这把锁从 `locks` 里删掉，再按公式重算。**只收回这把锁带来的捐赠**，别的锁上的捐赠还在（donate-multiple 要的就是这个）。

然后 `sema_up` 叫醒等锁的线程中优先级最高的，并且因为我的优先级刚降下来，`sema_up` 末尾的 `thread_preempt()` 会让我马上让出 CPU。

### 8.7 thread_set_priority：只改 base

```c
void
thread_set_priority (int new_priority) 
{
  struct thread *cur = thread_current ();
  enum intr_level old_level;

  if (thread_mlfqs)          /* MLFQS 模式下优先级由调度器算，忽略 */
    return;

  old_level = intr_disable ();
  cur->base_priority = new_priority;
  thread_update_priority (cur);
  intr_set_level (old_level);

  thread_preempt ();         /* 降低后可能有人比我高了 */
}
```

如果直接写 `cur->priority = new_priority`，被捐赠期间就会把捐赠“覆盖”掉（donate-lower 挂掉的原因）。`thread_get_priority()` 不用改，返回的就是实际优先级 `priority`。

### 8.8 和 MLFQS 的关系

`-o mlfqs` 模式下优先级由 MLFQS 公式自动计算，Pintos 文档规定这时**不做优先级捐赠**、`thread_set_priority` 也无效。所以上面每个函数都先判断 `thread_mlfqs`。priority-* 测试开头都有 `ASSERT (!thread_mlfqs);`，只在普通模式下跑。

---

## 9. 三个最难测试的逐步推演

建议上台前自己在纸上跟着画一遍，被追问时可以直接在黑板上画。

### 9.1 priority-donate-multiple（多重捐赠）

| 步骤 | 发生了什么 | main 的 locks | a.max | b.max | main.priority |
|---|---|---|---|---|---|
| 1 | main(31) 拿 a、拿 b | {a, b} | 0 | 0 | 31 |
| 2 | 创建线程 a(32)，它比 main 高，立刻运行，去拿锁 a → 阻塞，捐 32 | {a, b} | 32 | 0 | **32** |
| 3 | 创建线程 b(33)，立刻运行，拿锁 b → 阻塞，捐 33 | {a, b} | 32 | 33 | **33** |
| 4 | main 放 b：从 locks 删掉 b，重算 max(31, 32) | {a} | 32 | — | **32** |
| 5 | sema_up 叫醒线程 b(33) > 32，main 让出；b 跑完 | | | | |
| 6 | main 放 a：重算 max(31) | {} | — | — | **31** |
| 7 | 线程 a(32) > 31，抢占，跑完 | | | | |

如果第 4 步写成“恢复 base”，main 会直接变成 31——实际输出 `Actual priority: 31`，期望是 32。

### 9.2 priority-donate-nest（嵌套捐赠）

```
H(33) ──等──► 锁 b ──持有者──► M(32→33) ──等──► 锁 a ──持有者──► L(31→32→33)
```

| 步骤 | 发生了什么 | L | M |
|---|---|---|---|
| 1 | L(main, 31) 拿锁 a | 31 | — |
| 2 | M(32) 拿锁 b，再去拿锁 a → 阻塞；a.max=32，L 变 32 | 32 | 32 |
| 3 | H(33) 去拿锁 b → 阻塞；b.max=33，M 变 33；**沿 M.waiting_lock = a 继续**：a.max=33，L 变 33 | **33** | 33 |
| 4 | L 放 a → L 回到 31；M 拿到 a，跑；M 放 a、放 b → H 拿到 b 跑完；M 跑完 | 31 | |

如果只捐一层（第 3 步不沿链往下），L 停在 32，测试第二行输出 `Actual priority: 32`（期望 33）。donate-chain 是同样的道理，只是链有 7 层，而且每层旁边都有一个 interloper 等着插队：只捐一层的话 main 一直停在 3，每个 interloper 都能先跑完。

### 9.3 priority-donate-sema（等待中被捐赠）

| 步骤 | 发生了什么 | 信号量 waiters |
|---|---|---|
| 1 | L(32) 拿锁，然后 `sema_down` 阻塞 | [L 32] |
| 2 | M(34) `sema_down` 阻塞，有序插入排在 L 前面 | [M 34, L 32] |
| 3 | H(36) 去拿 L 的锁 → 阻塞，捐 36 给 L | [M 34, **L 36**] ← 顺序没变！ |
| 4 | main `sema_up` | 取队首 → 叫醒 M ✗；`list_min` 重新找 → 叫醒 L ✓ |

正确流程：L 醒来（36）→ “Thread L downed semaphore.” → L 放锁，优先级回到 32，H(36) 拿到锁 → “Thread H acquired lock.” → H `sema_up`（叫醒 M）、放锁 → “Thread H finished.” → M(34) → “Thread M finished.” → L(32) → “Thread L finished.” → main → “Main thread finished.”

我当时是在 `sema_up` 里临时加 `printf` 把等待队列打出来才看明白的：

```text
[debug] sema_up waiters: med(34) low(36)
```

low 已经是 36，却排在 med 后面。

---

## 10. 我踩过的坑（对应 PPT）

| # | 坑 | 现象 | 修复 | PPT |
|---|---|---|---|---|
| ① | 比较函数写成 `>=` | priority-fifo 输出 `15 15 15 …` | 改成严格 `>` | 第 3 页 |
| — | 在 `thread_wake`（时钟中断里）直接调 `thread_yield` | kernel panic：`assertion !intr_context () failed` | 改成 `intr_yield_on_return()` | 第 4 页 |
| ② | 放锁时直接恢复 `base_priority` | donate-multiple：`Actual priority: 31`（期望 32） | 删掉这把锁再按公式重算 | 第 8 页 |
| ③ | 只捐给直接持有者 | donate-nest：L 是 32（期望 33）；donate-chain 的 interloper 插队 | 沿 `waiting_lock → holder` 一路捐，最多 8 层 | 第 8 页 |
| ④ | `sema_up` 直接取队首 | donate-sema：M 先结束，L、H 没跑完 | `list_min` 重新找最高 | 第 9 页 |
| — | `thread_set_priority` 直接覆盖 `priority` | donate-lower：`Actual priority: 21`（期望 41） | 只改 base，再按公式重算 | 第 7 页 |

**kernel panic 的排查过程（PPT 第 4 页）**，被问到时可以这样讲：

1. 报错信息是 `Kernel PANIC at ../../threads/thread.c:354 in thread_yield(): assertion '!intr_context ()' failed.`，后面跟着一串 `Call stack` 地址。
2. 用 `backtrace kernel.o <地址>` 解析，结果只有一行 `debug_panic`。
3. 原因是 gcc 在 `-O` 优化下默认省略帧指针（frame pointer），而 Pintos 打印调用栈是靠帧指针一层层往上找的，链条第一层就断了。
4. 在 `src/Make.config` 的 `CFLAGS` 里临时加 `-fno-omit-frame-pointer`，`make clean` 重新编译，再崩一次，调用链就完整了：`idle → intr_entry → intr_handler → timer_interrupt → thread_wake → thread_yield`。
5. 一看就明白：`thread_wake` 是时钟中断调用的，中断里不能切换线程。改成 `intr_yield_on_return()`。

---

## 11. 上台讲解要点 + 问答准备

### 11.1 5 分钟里一定要讲清楚的三件事

1. **ready_list 有序 + 在三个地方检查抢占**（`>` 不能写成 `>=`）。
2. **捐赠的数据结构**：线程记持有的锁，锁记等它的最高优先级，`priority = max(base, 各锁的 max)`，一切变化都重算。
3. **等待队列在等待期间会“过期”**：`sema_up` 取出时要重新找最高的（donate-sema）。

其他的（反转的定义、感悟）时间不够就一句话带过。

### 11.2 可能被问到的问题

**Q1：为什么不在捐赠发生的时候直接调整信号量等待队列的顺序？**
捐赠时只知道“持锁线程是谁”，不知道它此刻挂在哪个信号量的等待队列上（`elem` 只有一个，但没有记录它属于哪个链表）。在 `sema_up` 取出时线性找一遍最高的最简单，等待队列一般也很短。

**Q2：嵌套捐赠为什么限制 8 层？**
防止锁链特别长或者出现环（死锁）时一直循环下去。Pintos 文档明确说可以设一个合理的上限（比如 8 层）；donate-chain 是 7 层，够用。

**Q3：为什么用“锁的列表”而不是课件说的“捐赠者列表”？**
捐赠是按锁收回的。记锁的话，放锁时 `list_remove` 一下再重算就行；记捐赠者的话，放锁时要遍历捐赠者列表，把所有在等这把锁的捐赠者删掉，还要处理嵌套捐赠时“间接捐赠者”的情况，更容易错。两种都能过测试，我觉得记锁更直接。

**Q4：`lock_release` 之后谁负责让出 CPU？**
`lock_release` 里调用的 `sema_up` 末尾有 `thread_preempt()`：放锁后我的优先级可能降了，被叫醒的等锁线程可能比我高，就会立刻让出。

**Q5：`thread_preempt` 里为什么要判断 `intr_context()`？**
`sema_up` 可能在中断处理程序里被调用（比如设备中断），中断里不能 `thread_yield`，只能 `intr_yield_on_return`。

**Q6：同优先级的线程怎么调度？**
FIFO 轮转：比较函数用严格 `>`，新入队的线程排在同优先级线程的最后；时间片用完（4 个 tick）就 `thread_yield` 重新排到队尾。

**Q7：被捐赠的线程如果正在就绪队列里，会发生什么？**
`thread_update_priority` 会把它从 `ready_list` 里摘下来，按新优先级重新插入，否则调度器还是按旧位置选人。

**Q8：一个线程能同时在等两把锁吗？**
不能。等锁意味着阻塞在那把锁的 `sema_down` 里，阻塞的线程不会再去拿另一把锁。所以 `waiting_lock` 一个指针就够了；但可以同时**持有**多把锁，所以 `locks` 是链表。

**Q9：为什么 `lock_acquire` 拿到锁以后要重新计算 `lock->max_priority`？**
这把锁上剩下的等待者原来是捐给前一个持有者的，现在应该改为捐给新持有者。如果不重算，`max_priority` 可能是已经拿到锁的那个线程自己的优先级（它刚从等待队列里出来），或者是 0，都不对。

**Q10：MLFQS 模式下捐赠还生效吗？**
不生效。Pintos 文档规定 MLFQS 下不做捐赠，优先级完全由 `recent_cpu` 和 `nice` 算出来，所以每个相关函数都先判断 `thread_mlfqs`。

**Q11：优先级反转除了捐赠还有别的办法吗？**
有，比如“优先级天花板”（priority ceiling）：给每把锁预先设定一个上限优先级，谁拿到锁就临时提升到这个上限。Pintos 要求的是优先级继承（捐赠）。

**Q12：你怎么调试的？**
三招：读 `.result` 里的 diff 看差在哪一行；在关键位置加 `printf`（比如打印信号量等待队列）；kernel panic 时用 `backtrace` 看调用栈（必要时加 `-fno-omit-frame-pointer`）。另外只跑单个测试 `make tests/threads/xxx.result`，不用每次跑十几分钟的 `make check`。

---

## 12. 名词速查

| 名词 | 一句话解释 |
|---|---|
| ready_list | 就绪队列，READY 状态的线程在这里排队，我改成了按优先级降序 |
| 抢占 preemption | 更高优先级的线程出现时，当前线程马上让出 CPU |
| 时间片 time slice | 每个线程连续运行的最长时间，Pintos 是 4 个 tick |
| tick | 一次时钟中断，Pintos 每秒 100 个 |
| 中断上下文 | 正在处理中断，不能睡眠、不能切换线程 |
| `intr_yield_on_return` | 中断里“预约”一次让出 CPU，中断返回时生效 |
| 优先级反转 | 高优先级线程被低优先级线程持有的锁挡住，又被中优先级线程间接卡住 |
| 优先级捐赠 / 继承 | 等锁的线程把自己的优先级借给持锁线程 |
| 多重捐赠 | 一个线程持有多把锁，同时接受多份捐赠，取最高的 |
| 嵌套捐赠 | 捐赠沿着“等锁 → 持有者 → 持有者在等的锁”的链传递 |
| base_priority | 线程自己设置的原始优先级 |
| priority（实际优先级） | `max(base_priority, 所持每把锁的 max_priority)` |
| Mesa 管程 | signal 后被唤醒者不立即运行，要重新竞争锁 |
| 侵入式链表 | 链表节点嵌在结构体内部，用 `list_entry` 找回外层结构体 |
