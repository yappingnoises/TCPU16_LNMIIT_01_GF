from coros.bench import ADD, HALT, JMP, JZ, LOAD, SHL, SUB, XOR


def new_state():
    return {
        "pc": 0,
        "acc": 0,
        "ir": 0,
        "halted": 0,
        "run_stage1": 0,
        "run_sync": 0,
    }


def advance(program, state, external_run):
    old_stage1 = state["run_stage1"]
    run = state["run_sync"]
    state["run_stage1"] = external_run
    state["run_sync"] = old_stage1

    if run and not state["halted"]:
        current = program[state["pc"]]
        opcode, operand = current >> 5, current & 0x1F
        jump = False
        target = operand & 0x7

        if opcode == LOAD:
            state["acc"] = operand
        elif opcode == ADD:
            state["acc"] = (state["acc"] + operand) & 0xFFFF
        elif opcode == SUB:
            state["acc"] = (state["acc"] - operand) & 0xFFFF
        elif opcode == SHL:
            state["acc"] = (state["acc"] << (operand & 0x7)) & 0xFFFF
        elif opcode == XOR:
            state["acc"] ^= operand
        elif opcode == JMP:
            jump = True
        elif opcode == JZ and state["acc"] == 0:
            jump = True
        elif opcode == HALT:
            state["halted"] = 1

        state["ir"] = current
        state["pc"] = target if jump else (state["pc"] + 1) & 0x7
