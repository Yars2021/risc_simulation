.data:
    var_l 108
    var_o 111

.start:
    ; Output register is %rou ~ %rdi ~ %reg5
    mov %rou 72     ; H
    wr
    mov %rou 101    ; e
    wr
    mov %rou var_l  ; l
    wr
    mov %rdi var_l  ; l
    wr
    mov %rdi var_o  ; o
    wr
    mov %rdi 44     ; ,
    wr
    mov %reg5 32    ;
    wr
    mov %reg5 87    ; W
    wr
    mov %reg5 var_o ; o
    wr
    mov %rou 114    ; r
    wr
    mov %rou var_l  ; l
    wr
    mov %rou 100    ; d
    wr
    mov %rou 33     ; !
    wr
    hlt