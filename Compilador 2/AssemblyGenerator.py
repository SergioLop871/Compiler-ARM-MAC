from nodes import VarAccessNode, StringNode, NumberNode

class AssemblyGenerator:
    def __init__(self):
        self.instructions = []
        self.data_section = [
            "print_buffer: .skip 32",
            "newline: .ascii \"\\n\""
        ]
        self.label_counter = 0
        self.var_table = {}  # var_name -> label

    def new_label(self, base='label'):
        self.label_counter += 1
        return f'{base}_{self.label_counter}'

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f'No visit_{type(node).__name__} method')
    
    def visit_CallNode(self, node):
        if isinstance(node.node_to_call, VarAccessNode):
            func_name = node.node_to_call.var_name_tok.value.upper()

            if func_name == 'PRINT':
                arg = node.arg_nodes[0]

                if isinstance(arg, StringNode):
                    label = self.new_label("str")
                    self.data_section.append(f'{label}: .ascii "{arg.tok.value}\\n"')
                    self.instructions.append(f"    adr x1, {label}")
                    self.instructions.append(f"    add x1, x1, :lo12:{label}")
                    self.instructions.append(f"    mov x2, #{len(arg.tok.value)+1}")  # +1 por \n
                    self.instructions.append("    mov x0, #1")
                    self.instructions.append("    mov x16, #4")  # syscall write
                    self.instructions.append("    svc #0")
                    return

                elif isinstance(arg, (NumberNode, VarAccessNode)):
                    self.visit(arg)  # evalúa la expresión o carga el valor de la variable a x0
                    self.generate_print_syscall()
                    return

                else:
                    raise Exception("PRINT solo soporta strings o enteros por ahora")
            
            elif func_name == 'RUN':
                arg = node.arg_nodes[0]
                if not isinstance(arg, StringNode):
                    raise Exception("RUN solo acepta una cadena como nombre de archivo")

                filename = arg.tok.value

                try:
                    with open(filename, 'r') as f:
                        source = f.read()
                except FileNotFoundError:
                    raise Exception(f"Archivo '{filename}' no encontrado")

                # Importar el compilador completo
                from pebble import run

                result, error = run(filename, source, asm_generator=self)
                if error:
                    raise Exception(f"Error al ejecutar {filename}: {error}")
                return          

        raise Exception(f"Función '{func_name}' no soportada por el generador")
        
    def visit_ListNode(self, node):
        for element in node.element_nodes:
            self.visit(element)

    def visit_NumberNode(self, node):
        self.instructions.append(f"    mov x0, #{node.tok.value}")

    def visit_VarAssignNode(self, node):
        self.visit(node.value_node)
        var_name = node.var_name_tok.value
        label = self.var_table.get(var_name)
        if label is None:
            label = self.new_label(var_name)
            self.var_table[var_name] = label
            self.data_section.append(f"{label}: .quad 0")
        self.instructions.append(f"    adr x1, {label}")
        self.instructions.append(f"    add x1, x1, :lo12:{label}")
        self.instructions.append(f"    str x0, [x1]")

    def visit_VarAccessNode(self, node):
        var_name = node.var_name_tok.value
        label = self.var_table.get(var_name)
        if label is None:
            raise Exception(f"Variable '{var_name}' not defined")
        self.instructions.append(f"    adr x1, {label}")
        self.instructions.append(f"    add x1, x1, :lo12:{label}")
        self.instructions.append(f"    ldr x0, [x1]")

    def visit_BinOpNode(self, node):
        self.visit(node.left_node)
        self.instructions.append("    mov x1, x0")
        self.visit(node.right_node)
        op = node.op_tok.value
        if op == '+':
            self.instructions.append("    add x0, x1, x0")
        elif op == '-':
            self.instructions.append("    sub x0, x1, x0")
        elif op == '*':
            self.instructions.append("    mul x0, x1, x0")
        elif op == '/':
            self.instructions.append("    sdiv x0, x1, x0")
        elif op == '==':
            self.instructions.append("    cmp x1, x0")
            self.instructions.append("    cset x0, eq")
        elif op == '!=':
            self.instructions.append("    cmp x1, x0")
            self.instructions.append("    cset x0, ne")
        elif op == '<':
            self.instructions.append("    cmp x1, x0")
            self.instructions.append("    cset x0, lt")
        elif op == '<=':
            self.instructions.append("    cmp x1, x0")
            self.instructions.append("    cset x0, le")
        elif op == '>':
            self.instructions.append("    cmp x1, x0")
            self.instructions.append("    cset x0, gt")
        elif op == '>=':
            self.instructions.append("    cmp x1, x0")
            self.instructions.append("    cset x0, ge")
        elif op == 'AND':
            self.instructions.append("    and x0, x1, x0")
        elif op == 'OR':
            self.instructions.append("    orr x0, x1, x0")
        else:
            raise Exception(f"Operación '{op}' no soportada")

    def visit_UnaryOpNode(self, node):
        self.visit(node.node)
        op = node.op_tok.value
        if op == '-':
            self.instructions.append("    neg x0, x0")
        elif op == 'NOT':
            self.instructions.append("    cmp x0, #0")
            self.instructions.append("    cset x0, eq")
        else:
            raise Exception(f"Operador unario '{op}' no soportado")

    def visit_IfNode(self, node):
        end_label = self.new_label("endif")
        for condition, body, _ in node.cases:  # ← Nota el "_"
            next_label = self.new_label("else")
            self.visit(condition)
            self.instructions.append("    cmp x0, #0")
            self.instructions.append(f"    beq {next_label}")
            self.visit(body)
            self.instructions.append(f"    b {end_label}")
            self.instructions.append(f"{next_label}:")

        if node.else_case:
            self.visit(node.else_case[0])  # ← else_case también es una tupla (body, is_block)

        self.instructions.append(f"{end_label}:")

    def visit_WhileNode(self, node):
        start_label = self.new_label("while_start")
        end_label = self.new_label("while_end")
        self.instructions.append(f"{start_label}:")
        self.visit(node.condition_node)
        self.instructions.append("    cmp x0, #0")
        self.instructions.append(f"    beq {end_label}")
        self.visit(node.body_node)
        self.instructions.append(f"    b {start_label}")
        self.instructions.append(f"{end_label}:")

    def visit_ForNode(self, node):
        loop_var = node.var_name_tok.value
        loop_label = self.new_label("for_loop")
        end_label = self.new_label("for_end")

        self.visit(node.start_value_node)
        self.instructions.append("    mov x1, x0")
        label = self.var_table.get(loop_var)
        if label is None:
            label = self.new_label(loop_var)
            self.var_table[loop_var] = label
            self.data_section.append(f"{label}: .quad 0")
        self.instructions.append(f"    adr x2, {label}")
        self.instructions.append(f"    add x2, x2, :lo12:{label}")
        self.instructions.append("    str x1, [x2]")

        self.visit(node.end_value_node)
        self.instructions.append("    mov x3, x0")

        if node.step_value_node:
            self.visit(node.step_value_node)
            self.instructions.append("    mov x4, x0")
        else:
            self.instructions.append("    mov x4, #1")

        self.instructions.append(f"{loop_label}:")
        self.instructions.append("    ldr x1, [x2]")
        self.instructions.append("    cmp x1, x3")
        self.instructions.append(f"    bge {end_label}")
        self.visit(node.body_node)
        self.instructions.append("    ldr x1, [x2]")
        self.instructions.append("    add x1, x1, x4")
        self.instructions.append("    str x1, [x2]")
        self.instructions.append(f"    b {loop_label}")
        self.instructions.append(f"{end_label}:")
    
    def generate_print_syscall(self):
        # x0: número a imprimir
        # Convertir entero a string (buffer en x0, número en x1)
        self.instructions.append("    mov x1, x0")                          # número en x1
        self.instructions.append("    adr x0, print_buffer")               # dirección de buffer
        self.instructions.append("    bl int_to_str")                      # convierte int a string

        # Llamada al sistema: write(stdout, buffer, length)
        self.instructions.append("    mov x0, #1")                         # stdout
        self.instructions.append("    mov x2, x1")                         # longitud devuelta en x1
        self.instructions.append("    mov x16, #4")                        # syscall write (0x2000004) → solo 4 para Apple
        self.instructions.append("    svc #0")

        # Imprimir salto de línea manualmente
        self.instructions.append("    adr x1, newline")                    # dirección de newline
        self.instructions.append("    mov x2, #1")                         # longitud
        self.instructions.append("    mov x0, #1")                         # stdout
        self.instructions.append("    mov x16, #4")                        # syscall write
        self.instructions.append("    svc #0")
        
    def write_to_file(self, filename):
        with open(filename, 'w') as f:
            f.write('.global _main\n.data\n.align 2\n')
            for line in self.data_section:
                f.write(line + '\n')
            f.write('.text\n_main:\n')
            for line in self.instructions:
                f.write(line + '\n')

            f.write('\n// --- Función auxiliar: int_to_str ---\n')
            f.write('int_to_str:\n')
            f.write('    stp x29, x30, [sp, #-16]!\n')
            f.write('    mov x29, sp\n')
            f.write('    mov x2, x0\n')     # buffer
            f.write('    mov x3, x1\n')     # número
            f.write('    mov x4, #0\n')     # índice

            f.write('    cmp x3, #0\n')
            f.write('    b.ne convert_loop\n')
            f.write('    mov w5, #\'0\'\n')
            f.write('    strb w5, [x2]\n')
            f.write('    mov x1, #1\n')
            f.write('    b done\n')

            f.write('convert_loop:\n')
            f.write('    mov x5, x3\n')
            f.write('    mov x6, #10\n')
            f.write('    udiv x7, x5, x6\n')
            f.write('    msub x6, x7, x6, x5\n')
            f.write('    add x6, x6, #\'0\'\n')
            f.write('    strb w6, [x2, x4]\n')
            f.write('    add x4, x4, #1\n')
            f.write('    mov x3, x7\n')
            f.write('    cmp x3, #0\n')
            f.write('    b.ne convert_loop\n')

            f.write('    mov x5, x4\n')
            f.write('    sub x5, x5, #1\n')
            f.write('    mov x6, #0\n')

            f.write('rev_loop:\n')
            f.write('    cmp x6, x5\n')
            f.write('    b.ge done_rev\n')
            f.write('    ldrb w7, [x2, x6]\n')
            f.write('    ldrb w8, [x2, x5]\n')
            f.write('    strb w8, [x2, x6]\n')
            f.write('    strb w7, [x2, x5]\n')
            f.write('    add x6, x6, #1\n')
            f.write('    sub x5, x5, #1\n')
            f.write('    b rev_loop\n')

            f.write('done_rev:\n')
            f.write('done:\n')
            f.write('    mov x1, x4\n')   # longitud del string
            f.write('    ldp x29, x30, [sp], #16\n')
            f.write('    ret\n')
