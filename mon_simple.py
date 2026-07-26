import sys
import re

class MissionSyntaxError(Exception):
    pass

def canonicalize(source: str) -> str:
    token_pattern = re.compile(
        r'(?P<SPACE>\s+)|'
        r'(?P<STR>"[^"\n]*")|'
        r'(?P<BADSTR>"[^"\n]*)|'
        r'(?P<INT>[0-9_]+)|'
        r'(?P<ID>[A-Za-z0-9_]+)|'
        r'(?P<CREW>@[A-Za-z0-9_]*)|'
        r'(?P<SYM>[{}=;])|'
        r'(?P<ERR>.)'
    )

    tokens = []
    for m in token_pattern.finditer(source):
        kind = m.lastgroup
        val = m.group(kind)
        if kind == 'SPACE': 
            continue
        if kind == 'BADSTR': 
            raise MissionSyntaxError('Error: Unterminated string')
        if kind == 'ERR': 
            raise MissionSyntaxError(f"Error: Unexpected character '{val}'")
        tokens.append((kind, val))

    if not tokens:
        raise MissionSyntaxError("Error: Empty file")

    if tokens[0][1] != 'mission':
        raise MissionSyntaxError(f"Error: Expected 'mission', got '{tokens[0][1]}'")
    
    if len(tokens) < 2 or tokens[1][1] != '{':
        raise MissionSyntaxError("Error: Expected '{' after 'mission'")

    obj = {}
    i = 2
    first = True

    while i < len(tokens):
        if tokens[i][1] == '}':
            i += 1
            break

        if not first:
            if tokens[i][1] != ';':
                raise MissionSyntaxError("Error: Expected ';' between entries")
            i += 1
            if i >= len(tokens):
                raise MissionSyntaxError("Error: Expected '}' to close mission object")
            if tokens[i][1] == '}':
                raise MissionSyntaxError("Error: Trailing semicolon before '}' is not allowed")

        if tokens[i][0] != 'ID' or not re.match(r'^[a-z]+$', tokens[i][1]):
            raise MissionSyntaxError(f'Error: Invalid key "{tokens[i][1]}"')
        
        k = tokens[i][1]
        if k in obj:
            raise MissionSyntaxError(f'Error: Duplicate key "{k}"')
        i += 1

        if i >= len(tokens) or tokens[i][1] != '=':
            raise MissionSyntaxError(f'Error: Expected \'=\' after key "{k}"')
        i += 1

        if i >= len(tokens):
            raise MissionSyntaxError(f'Error: Expected value for key "{k}"')
        
        v_kind, v_val = tokens[i]
        
        if v_kind == 'INT':
            if v_val.startswith('0') and v_val != '0':
                raise MissionSyntaxError(f'Error: Invalid integer "{v_val}"')
            if v_val.startswith('_') or v_val.endswith('_') or '__' in v_val:
                raise MissionSyntaxError(f'Error: Invalid integer "{v_val}"')
            val = v_val.replace('_', '')
        elif v_kind == 'STR':
            val = v_val
        elif v_kind == 'CREW':
            if not re.match(r'^@[a-z]+$', v_val):
                raise MissionSyntaxError(f'Error: Invalid crew identifier "{v_val}"')
            val = v_val
        elif v_kind == 'ID' and v_val in ('yes', 'no'):
            val = v_val
        else:
            raise MissionSyntaxError(f'Error: Unrecognized value "{v_val}" for key "{k}"')
        
        obj[k] = val
        i += 1
        first = False

    if i < len(tokens):
        raise MissionSyntaxError(f"Error: Unexpected token '{tokens[i][1]}' after mission block")

    if not obj:
        return "mission {}"

    lines = ["mission {"]
    for key in sorted(obj.keys()):
        lines.append(f"    {key} = {obj[key]};")
    
    if len(lines) > 1:
        lines[-1] = lines[-1][:-1]
        
    lines.append("}")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 mon_simple.py <file.mon>", file=sys.stderr)
        sys.exit(1)

    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            source = f.read()
    except OSError as exc:
        print(f"Error: cannot read file: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        print(canonicalize(source))
    except MissionSyntaxError as exc:
        print(f"{exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()