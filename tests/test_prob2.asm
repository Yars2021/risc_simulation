.data:
    result 0
    limit 40

.start:
    mov %rax 1
    mov %rbx 1

    .loop:
        mov %rcx %rax
        add %rcx %rbx

        mov %rax %rbx
        mov %rbx %rcx

        mod %rcx 2
       ; cmp %rcx 0
       ; jne .continue

        add result %rbx

        .continue:
            cmp %rbx limit
            jnl .print_ans
            jmp .loop

    .print_ans:

    hlt