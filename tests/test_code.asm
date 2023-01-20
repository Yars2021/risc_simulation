.data:
    var_1 "3"

.start:
    mov %rdi var_1
    cmp %rdi %rsi
    je .end

    mov var_1 64

    .end:
        hlt