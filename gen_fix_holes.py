import io
# 1) el generador: un solo hueco de anillo (r10 se conserva hasta la cola)
p = "gen_vstub_guard.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('B("4dc89df9000000")', '')
s = s.replace("""B("498b8798000000")                      # mov rax, [r15+0x98]
B("492b8790000000")                      # sub rax, [r15+0x90]""",
"""B("498b8798000000")                      # mov rax, [r15+0x98]
B("492b8790000000")                      # sub rax, [r15+0x90]""")
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("gen listo")
