# Lab3：Pintos Project 1（Threads）

`src/threads` 下 `make check` 的 27 个测试全部通过（alarm 6 + priority 12 + mlfqs 9）。

## 文件说明

| 文件 | 说明 |
|---|---|
| `作业3.1实验报告.docx` | 实验报告（Word，可编辑）。第二节留了 make check 截图的位置，需要在虚拟机里自己截图后插入 |
| `作业3.1实验报告.md` | 报告的 Markdown 原稿，内容和 docx 一样 |
| `作业3.2-priority讲解.pptx` | 作业 3.2 上台讲解用的 PPT（8 页，约 5 分钟，讲 priority-*），每页讲稿在备注里 |
| `作业3.2讲稿.md` | 逐页讲稿 + 可能被问到的问题 |
| `修改后的源文件/src/...` | 只包含改动过的 7 个文件，目录结构和 `pintos/src` 一致 |
| `lab3.patch` | 相对于课程原始 `pintos (1).tar.gz` 的补丁 |
| `pintos-lab3.tar.gz` | 打好补丁的完整 pintos 源码（不含编译产物） |

改动的文件：`devices/timer.c`、`threads/thread.c`、`threads/thread.h`、`threads/synch.c`、`threads/synch.h`、`threads/Make.vars`（`--bochs` 改成 `--qemu`），以及新增的 `threads/fixed-point.h`。

## 在虚拟机里使用

虚拟机里的 pintos 已经有 lab2 的改动（`timer.c`、`thread.c`），`lab3.patch` 是基于原始代码生成的，直接打补丁会冲突，所以直接覆盖文件更省事：

```bash
# 假设虚拟机里 pintos 在 ~/pintos/pintos，修改后的源文件已经复制到 ~/lab3
cp -r ~/lab3/修改后的源文件/src/* ~/pintos/pintos/src/
cd ~/pintos/pintos/src/threads
make clean && make
cd build && make check
```

也可以直接解压 `pintos-lab3.tar.gz` 得到一份新的完整代码。不加 -j 全部跑完要十几分钟（mlfqs 的测试比较慢）。单独跑一个测试：`make tests/threads/priority-donate-sema.result`。
