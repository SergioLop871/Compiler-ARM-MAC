.global _main
.data
.align 2
print_buffer: .skip 32
newline: .ascii "\n"
a_1: .quad 0
i_4: .quad 0
j_7: .quad 0
str_12: .ascii "El valor de a es 15\n"
.text
_main:
    mov x0, #10
    adr x1, a_1
    add x1, x1, :lo12:a_1
    str x0, [x1]
    mov x0, #0
    mov x1, x0
    adr x2, i_4
    add x2, x2, :lo12:i_4
    str x1, [x2]
    mov x0, #5
    mov x3, x0
    mov x4, #1
for_loop_2:
    ldr x1, [x2]
    cmp x1, x3
    bge for_end_3
    adr x1, i_4
    add x1, x1, :lo12:i_4
    ldr x0, [x1]
    mov x1, x0
    adr x0, print_buffer
    bl int_to_str
    mov x0, #1
    mov x2, x1
    mov x16, #4
    svc #0
    adr x1, newline
    mov x2, #1
    mov x0, #1
    mov x16, #4
    svc #0
    ldr x1, [x2]
    add x1, x1, x4
    str x1, [x2]
    b for_loop_2
for_end_3:
    mov x0, #0
    mov x1, x0
    adr x2, j_7
    add x2, x2, :lo12:j_7
    str x1, [x2]
    adr x1, a_1
    add x1, x1, :lo12:a_1
    ldr x0, [x1]
    mov x3, x0
    mov x0, #2
    mov x4, x0
for_loop_5:
    ldr x1, [x2]
    cmp x1, x3
    bge for_end_6
    adr x1, j_7
    add x1, x1, :lo12:j_7
    ldr x0, [x1]
    mov x1, x0
    adr x0, print_buffer
    bl int_to_str
    mov x0, #1
    mov x2, x1
    mov x16, #4
    svc #0
    adr x1, newline
    mov x2, #1
    mov x0, #1
    mov x16, #4
    svc #0
    ldr x1, [x2]
    add x1, x1, x4
    str x1, [x2]
    b for_loop_5
for_end_6:
while_start_8:
    adr x1, a_1
    add x1, x1, :lo12:a_1
    ldr x0, [x1]
    mov x1, x0
    mov x0, #0
    cmp x1, x0
    cset x0, ne
    cmp x0, #0
    beq while_end_9
    adr x1, a_1
    add x1, x1, :lo12:a_1
    ldr x0, [x1]
    mov x1, x0
    adr x0, print_buffer
    bl int_to_str
    mov x0, #1
    mov x2, x1
    mov x16, #4
    svc #0
    adr x1, newline
    mov x2, #1
    mov x0, #1
    mov x16, #4
    svc #0
    adr x1, a_1
    add x1, x1, :lo12:a_1
    ldr x0, [x1]
    mov x1, x0
    mov x0, #2
    sub x0, x1, x0
    adr x1, a_1
    add x1, x1, :lo12:a_1
    str x0, [x1]
    b while_start_8
while_end_9:
    mov x0, #10
    adr x1, a_1
    add x1, x1, :lo12:a_1
    str x0, [x1]
    adr x1, a_1
    add x1, x1, :lo12:a_1
    ldr x0, [x1]
    mov x1, x0
    mov x0, #5
    add x0, x1, x0
    adr x1, a_1
    add x1, x1, :lo12:a_1
    str x0, [x1]
    adr x1, a_1
    add x1, x1, :lo12:a_1
    ldr x0, [x1]
    mov x1, x0
    mov x0, #15
    cmp x1, x0
    cset x0, eq
    cmp x0, #0
    beq else_11
    adr x1, str_12
    add x1, x1, :lo12:str_12
    mov x2, #20
    mov x0, #1
    mov x16, #4
    svc #0
    b endif_10
else_11:
endif_10:

// --- Función auxiliar: int_to_str ---
int_to_str:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    mov x2, x0
    mov x3, x1
    mov x4, #0
    cmp x3, #0
    b.ne convert_loop
    mov w5, #'0'
    strb w5, [x2]
    mov x1, #1
    b done
convert_loop:
    mov x5, x3
    mov x6, #10
    udiv x7, x5, x6
    msub x6, x7, x6, x5
    add x6, x6, #'0'
    strb w6, [x2, x4]
    add x4, x4, #1
    mov x3, x7
    cmp x3, #0
    b.ne convert_loop
    mov x5, x4
    sub x5, x5, #1
    mov x6, #0
rev_loop:
    cmp x6, x5
    b.ge done_rev
    ldrb w7, [x2, x6]
    ldrb w8, [x2, x5]
    strb w8, [x2, x6]
    strb w7, [x2, x5]
    add x6, x6, #1
    sub x5, x5, #1
    b rev_loop
done_rev:
done:
    mov x1, x4
    ldp x29, x30, [sp], #16
    ret
