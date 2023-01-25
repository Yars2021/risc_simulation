.start:
    rd
    mov %rou %rin
    cmp %rou 0
    je .exit
    wr
    jmp .start

    .exit:
        hlt