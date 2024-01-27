from flask import Flask, render_template, request
import importlib
import re
import PIL.ImageFont
from pathlib import Path

THIS_FOLDER = Path(__file__).parent.resolve()
app = Flask(__name__)


def tokenize(formula: str) -> list:
    tokens = []
    token = ""
    i = 0
    is_name = False
    while i < len(formula):
        if formula[i].isspace():
            is_name = False
            if token != "":
                tokens.append(token)
                token = ""
            i += 1
            continue
        if formula[i] == "(" or formula[i] == ")":
            is_name = False
            if token != "":
                tokens.append(token)
                token = ""
            tokens.append(formula[i])
            i += 1
            continue
        is_operator = False
        if not is_name:
            for op in operators:
                if formula[i:i + len(op)] == op:
                    tokens.append(op)
                    i += len(op)
                    is_operator = True
                    break
                isalt = False
                for alt in operator_dic.get(op):
                    if formula[i:i + len(alt)] == alt:
                        tokens.append(op)
                        i += len(alt)
                        is_operator = True
                        isalt = True
                        break
                if isalt:
                    break
        if not is_operator:
            if formula[i] != "\\":
                is_name = True
                token += formula[i]
            i += 1
    if token != "":
        tokens.append(token)
    return tokens


def add_priority(tokens: list):
    formula = tokens
    for operator in operators:
        found = False
        is_not_neg = operator != "not"
        if operator == "imply" or operator == "nimply":
            formula = handle_implication(formula, operator)
            continue
        i = 0
        while i < len(formula):
            if found:
                found = False
                i += 1
                continue
            token = formula[i]
            if token == operator:
                offset = 0
                if formula[i + 1] == "(":
                    formula.insert(find_matching_paren(formula, i + 2), ")")
                else:
                    if not is_not_neg:
                        while formula[i + 1 + offset] == "not":
                            offset += 1
                        if (offset + 1) % 2 == 0:
                            for j in range(offset + 1):
                                formula.pop(i)
                        else:
                            for j in range(offset):
                                formula.pop(i)
                            if formula[i + 1] == "(":
                                formula.insert(find_matching_paren(formula, i + 2), ")")
                            else:
                                formula.insert(i + 2, ")")
                    else:
                        formula.insert(i + 2 + offset, ")")
                if formula[i - 1] == ")" and is_not_neg:
                    formula.insert(find_reverse_paren(formula, i - 2), "(")
                    found = True
                elif (offset + 1) % 2 != 0:
                    formula.insert(i - is_not_neg, "(")
                    found = True
            i += 1
    result = remove_not(parse(formula))
    if type(result) is not list:
        return [result]
    return result


def handle_implication(tokens, operator):
    formula = tokens.copy()
    found = False
    i = len(formula) - 1
    while i >= 0:
        if found:
            found = False
            i -= 1
            continue
        token = formula[i]
        if token == operator:
            if formula[i + 1] == "(":
                formula.insert(find_matching_paren(formula, i + 2), ")")
            else:
                formula.insert(i + 2, ")")
            if formula[i - 1] == ")":
                formula.insert(find_reverse_paren(formula, i - 2), "(")
                found = True
            else:
                formula.insert(i - 1, "(")
                found = True
        i -= 1
    return formula


def remove_not(formula: list) -> list:
    if type(formula) is not list or len(formula) == 1:
        return formula
    if len(formula) == 2:
        if type(formula[1]) is not list or len(formula[1]) == 1:
            return formula
        if len(formula[1]) == 2:
            return remove_not(formula[1][1])
        return [formula[0], remove_not(formula[1])]
    return [remove_not(formula[0]), formula[1], remove_not(formula[2])]


def parse(formula: list) -> list:
    new = []
    i = 0
    while i < len(formula):
        token = formula[i]
        if token == "(":
            end = find_matching_paren(formula, i + 1)
            new.append(parse(formula[i + 1:end]))
            i = end
        else:
            new.append(token)
        i += 1
    if len(new) == 1 and type(new[0]) is list:
        return new[0]
    return new


def find_reverse_paren(tokens, end):
    count = 1
    for i in range(end, -1, -1):
        if tokens[i] == ')':
            count += 1
        elif tokens[i] == '(':
            count -= 1
            if count == 0:
                return i
    raise ValueError("Unmatched closing parenthesis")


def find_matching_paren(tokens, start):
    count = 1
    for i in range(start, len(tokens)):
        if tokens[i] == '(':
            count += 1
        elif tokens[i] == ')':
            count -= 1
            if count == 0:
                return i
    raise ValueError("Unmatched opening parenthesis: ", tokens)


def find_vars(formula: list):
    variables = []
    for elm in formula:
        if type(elm) is list:
            new_var = find_vars(elm)
            for val in new_var:
                if val not in variables:
                    variables.append(val)
        elif elm not in operators and elm not in variables:
            variables.append(elm)
    return sorted(variables)


def negate_bfs(formula):
    queue = [formula]
    if formula[0] == "not":
        print_formula(['not', formula])
        print_formula(formula[1])
        return
    else:
        print_formula(['not', formula], q=queue, color=True)
    while queue:
        ref = queue[0]
        if len(ref) == 1:
            ref[:] = ["not", ref]
        elif len(ref) == 2:
            if type(ref[1]) is list:
                # ref.pop(0)
                if len(ref[1]) == 1:
                    ref[0] = ref[1][0]
                    ref.pop()
                    queue.append(ref)
                elif len(ref[1]) == 2:
                    ref[0] = ref[1][1]
                    ref.pop()
                else:
                    ref[0] = ref[1][0]
                    ref.append(ref[1][2])
                    ref[1] = ref[1][1]
                    queue.append(ref)
        else:
            if ref[1] == "nand":
                ref[1] = "and"
            elif ref[1] == "nor":
                ref[1] = "or"
            elif ref[1] == "nimply":
                ref[1] = "imply"
            elif ref[1] == "xor":
                ref[1] = "equiv"
            elif ref[1] == "and":
                ref[1] = "or"
                if type(ref[0]) is not list or len(ref[0]) != 2:
                    ref[0] = ["not", ref[0]]
                    queue.append(ref[0])
                else:
                    ref[0] = ref[0][1]
                if type(ref[2]) is not list or len(ref[2]) != 2:
                    ref[2] = ["not", ref[2]]
                    queue.append(ref[2])
                else:
                    ref[2] = ref[2][1]
            elif ref[1] == "or":
                ref[1] = "and"
                if type(ref[0]) is not list or len(ref[0]) != 2:
                    ref[0] = ["not", ref[0]]
                    queue.append(ref[0])
                else:
                    ref[2] = ref[0][1]
                if type(ref[2]) is not list or len(ref[2]) != 2:
                    ref[2] = ["not", ref[2]]
                    queue.append(ref[2])
                else:
                    ref[2] = ref[2][1]
            elif ref[1] == "imply":
                ref[1] = "and"
                if type(ref[2]) is not list or len(ref[2]) != 2:
                    ref[2] = ["not", ref[2]]
                    queue.append(ref[2])
                else:
                    ref[2] = ref[2][1]
            elif ref[1] == "equiv":
                ref[1] = "or"
                temp0 = ref[0]
                if type(ref[2]) is not list or len(ref[2]) != 2:
                    ref[0] = [ref[0], "and", ["not", ref[2]]]
                    queue.append(ref[0][2])
                else:
                    ref[0] = [ref[0], "and", ref[2][1]]
                if type(temp0) is not list or len(temp0) != 2:
                    ref[2] = [ref[2], "and", ["not", temp0]]
                    queue.append(ref[2][2])
                else:
                    ref[2] = [ref[2], "and", temp0[1]]
            printout = True
            for elm in queue:
                if elm == queue[0]:
                    continue
                if elm[0] != "not":
                    printout = False
                    break
            if printout:
                print_formula(formula, q=queue, color=True)
        queue.pop(0)
    # print_formula(formula)


def negate(formula):
    result = []
    if type(formula) is list:
        if len(formula) == 1:
            result.append(["not", formula[0]])
        elif len(formula) == 2:
            result.append(formula[1])
        else:
            if formula[1] == "nand":
                result.append([formula[0], "and", formula[2]])
            elif formula[1] == "nor":
                result.append([formula[0], "or", formula[2]])
            elif formula[1] == "nimply":
                result.append(imply(formula[0], formula[2]))
            elif formula[1] == "xor":
                result.append(equiv(formula[0], formula[2]))
            elif formula[1] == "and":
                result.append([negate(formula[0]), "or", negate(formula[2])])
            elif formula[1] == "or":
                result.append([negate(formula[0]), "and", negate(formula[2])])
            elif formula[1] == "imply":
                result.append([formula[0], "and", negate(formula[2])])
            elif formula[1] == "equiv":
                result.append(negate([[formula[0], "imply", formula[2]], 'and', [formula[2], "imply", formula[0]]]))
    else:
        result.append(["not", formula])
    if len(result) == 1:  # and type(result[0])==list:
        return result[0]
    return result


def equiv(A: list, B: list):
    return [imply(A, B), "and", imply(B, A)]


def imply(A: list, B: list):
    return [negate(A), "or", B]


def oor(A: list, B: list):
    if len(A) == 1 and len(B) == 1:
        return [A[0], "or", B[0]]
    if len(A) == 1 and len(B) == 2:
        return [A[0], "or", B]
    if len(A) == 2 and len(B) == 1:
        return [A, "or", B[0]]
    if len(A) == 2 and len(B) == 2:
        return [A, "or", B]
    if len(A) == 1 and len(B) == 3:
        if B[1] == "and":
            return [[A[0], "or", to_cnf(B[0])], "and", [A[0], "or", to_cnf(B[2])]]
        return [A[0], "or", to_cnf(B)]
    if len(A) == 2 and len(B) == 3:
        if B[1] == "and":  # A
            return [[A, "or", to_cnf(B[0])], "and", [A, "or", to_cnf(B[2])]]  # [2]
        # return [[A,"or",to_cnf(B[0])],"or",[A,"or",to_cnf(B[2])]]
        return [A, "or", to_cnf(B)]
    if len(A) == 3 and len(B) == 1:
        if A[1] == "and":
            return [[to_cnf(A[0]), "or", B[0]], "and", [to_cnf(A[2]), "or", B[0]]]
        return [to_cnf(A), "or", B[0]]
    if len(A) == 3 and len(B) == 2:
        if A[1] == "and":
            return [[to_cnf(A[0]), "or", B], "and", [to_cnf(A[2]), "or", B]]
        # return [[to_cnf(A[0]),"or",B],"or",[to_cnf(A[2]),"or",B]]
        return [to_cnf(A), "or", B]
    if len(A) == 3 and len(B) == 3:
        if A[1] == "or" and B[1] == "or":
            return [to_cnf(A), "or", to_cnf(B)]
        if A[1] == "or":
            return [[to_cnf(A), "or", B[0]], "and", [to_cnf(A), "or", B[2]]]
        if B[1] == "or":
            return [[A[0], "or", to_cnf(B)], "and", [A[2], "or", to_cnf(B)]]
        return to_cnf([[[[A[0], "or", B[0]]], "and", [[A[0], "or", B[2]]]], "and",
                       [[[A[2], "or", B[0]]], "and", [[A[2], "or", B[2]]]]])
    return [A, "and", B]


def nand(A: list, B: list):
    return negate([A, "and", B])


def nor(A: list, B: list):
    return negate([A, "or", B])


def nimply(A: list, B: list):
    return negate([A, "imply", B])


def xor(A: list, B: list):
    return negate([A, "equiv", B])


def to_cnf(formula):
    if type(formula) is not list:
        return [formula]
    if len(formula) == 1:
        return to_cnf(formula[0])
    elif len(formula) == 2:
        if len(formula[1]) == 1 or formula[1] in var:
            return formula
        # if len(formula[1])==2:
        # return to_cnf(formula[1])
        return to_cnf(negate(formula[1]))
    else:
        if formula[1] == "and":
            return [to_cnf(formula[0]), "and", to_cnf(formula[2])]
        elif formula[1] == "or":
            return oor(to_cnf(formula[0]), to_cnf(formula[2]))
        elif formula[1] == "imply":
            return to_cnf(imply(formula[0], formula[2]))
        elif formula[1] == "equiv":
            return to_cnf(equiv(formula[0], formula[2]))
        elif formula[1] == "nand":
            return to_cnf(nand(formula[0], formula[2]))
        elif formula[1] == "nor":
            return to_cnf(nor(formula[0], formula[2]))
        elif formula[1] == "nimply":
            return to_cnf(nimply(formula[0], formula[2]))
        elif formula[1] == "xor":
            return to_cnf(xor(formula[0], formula[2]))
        else:
            return None


def simplify_terms(cnf: list):
    new_cnf = []
    if len(cnf) == 2 and cnf[0] == "not":
        return cnf
    for term in cnf:
        if type(term) is list:
            terms = simplify_terms(term)
            if terms in new_cnf:
                new_cnf.pop()
                continue
            if len(terms) == 2:
                new_cnf.append(terms)
                continue
            for t in terms:
                new_cnf.append(t)
        elif term == "and" or term == "or":
            new_cnf.append(term)
        else:
            new_cnf.append(term)
    final_cnf = []
    for term in new_cnf:
        if type(term) is list:
            for t in term:
                final_cnf.append(t)
        else:
            final_cnf.append(term)
    return final_cnf


def handle_temp(temp, new_temp):
    i = 0
    while i < len(temp):
        if temp[i] == "not":
            if ["not", temp[i + 1]] not in new_temp:
                new_temp.append(["not", temp[i + 1]])
            else:
                new_temp.pop()
            i += 1
        elif temp[i] not in new_temp or temp[i] in operators:
            new_temp.append(temp[i])
        else:
            new_temp.pop()
        i += 1


def simplify(cnf: list):
    new_cnf = []
    temp = []
    for elm in cnf:
        if elm == "and":
            new_temp = []
            if "not" not in temp:
                for t in temp:
                    if t not in new_temp or t in operators:
                        new_temp.append(t)
                    else:
                        new_temp.pop()
                temp = new_temp
            else:
                handle_temp(temp, new_temp)
                temp = []
                for element in new_temp:
                    if type(element) is list:
                        if element[1] in new_temp:
                            temp = []
                            break
                        for e in element:
                            temp.append(e)
                        continue
                    temp.append(element)
            if temp not in new_cnf and temp != []:
                new_cnf.append(temp)
                new_cnf.append("and")
            temp = []
        else:
            temp.append(elm)
    new_temp = []
    if "not" not in temp:
        for t in temp:
            if t not in new_temp or t in operators:
                new_temp.append(t)
            else:
                new_temp.pop()
        temp = new_temp
    else:
        handle_temp(temp, new_temp)
        temp = []
        for elm in new_temp:
            if type(elm) is list:
                if elm[1] in new_temp:
                    temp = []
                    if new_cnf:
                        new_cnf.pop()
                    break
                for e in elm:
                    temp.append(e)
                continue
            temp.append(elm)
    if temp not in new_cnf and temp != []:
        new_cnf.append(temp)
    elif new_cnf and new_cnf[-1] == "and":
        new_cnf.pop()
    # remove duplicate clauses
    duplicates = []
    i = 0
    while i < len(new_cnf):
        clause = new_cnf[i]
        if clause == "and":
            i += 1
            continue
        new_clause = set()
        if "not" in clause:
            j = 0
            while j < len(clause):
                if clause[j] == "not":
                    j += 1
                    new_clause.add(frozenset(["not", clause[j]]))
                else:
                    new_clause.add(clause[j])
                j += 1
        else:
            new_clause = set(clause)
        if set(new_clause) in duplicates:
            new_cnf.pop(i)
            new_cnf.pop(i - 1)
        else:
            duplicates.append(new_clause)
            i += 1
    if new_cnf and new_cnf[-1] == "and":
        new_cnf.pop()
    return new_cnf


def remove_imply(formula, q):
    if type(formula) is not list:
        return formula
    if len(formula) == 1:
        return remove_imply(formula[0], q)
    elif len(formula) == 2:
        if len(formula[1]) == 1 or formula[1] in var:
            return formula
        return ["not", remove_imply(formula[1], q)]
    else:
        if formula[1] == "and":
            return [remove_imply(formula[0], q), "and", remove_imply(formula[2], q)]
        elif formula[1] == "or":
            return [remove_imply(formula[0], q), "or", remove_imply(formula[2], q)]
        elif formula[1] == "imply":
            q.append(formula)
            ret = remove_imply(imply(formula[0], formula[2]), q)
            q.append(ret)
            return ret
        elif formula[1] == "equiv":
            q.append(formula)
            ret = remove_imply(equiv(formula[0], formula[2]), q)
            q.append(ret)
            return ret
        elif formula[1] == "nand":
            return [remove_imply(formula[0], q), "nand", remove_imply(formula[2], q)]
        elif formula[1] == "nor":
            return [remove_imply(formula[0], q), "nor", remove_imply(formula[2], q)]
        elif formula[1] == "nimply":
            return [remove_imply(formula[0], q), "nimply", remove_imply(formula[2], q)]
        elif formula[1] == "xor":
            return [remove_imply(formula[0], q), "xor", remove_imply(formula[2], q)]
        else:
            return None


def remove_neg(formula, q):
    if type(formula) is not list:
        return formula
    if len(formula) == 1:
        return to_cnf(formula[0])
    elif len(formula) == 2:
        if len(formula[1]) == 1 or formula[1] in var:
            return formula
        q.append(formula)
        ret = remove_neg(negate(formula[1]), q)
        q.append(ret)
        return ret
    else:
        if formula[1] == "and":
            return [remove_neg(formula[0], q), "and", remove_neg(formula[2], q)]
        elif formula[1] == "or":
            return [remove_neg(formula[0], q), "or", remove_neg(formula[2], q)]
        elif formula[1] == "nand":
            q.append(formula)
            ret = remove_neg(nand(formula[0], formula[2]), q)
            q.append(ret)
            return ret
        elif formula[1] == "nor":
            q.append(formula)
            ret = remove_neg(nor(formula[0], formula[2]), q)
            q.append(ret)
            return ret
        elif formula[1] == "nimply":
            q.append(formula)
            ret = remove_neg(nimply(formula[0], formula[2]), q)
            q.append(ret)
            return ret
        elif formula[1] == "xor":
            q.append(formula)
            ret = remove_neg(xor(formula[0], formula[2]), q)
            q.append(ret)
            return ret
        else:
            return None


def distribute(formula, q):
    if type(formula) is not list:
        return formula
    if len(formula) == 1:
        return to_cnf(formula[0])
    elif len(formula) == 2:
        if len(formula[1]) == 1 or formula[1] in var:
            return formula
        return distribute(negate(formula[1]), q)
    else:
        if formula[1] == "and":
            return [distribute(formula[0], q), "and", distribute(formula[2], q)]
        elif formula[1] == "or":
            q.append(formula)
            ref = (formula.copy(), len(q) - 1)
            ret = oor(distribute(formula[0], q), distribute(formula[2], q))
            if ref[0][1] == "or" and ret[1] == "and":
                q.append(ret)
            else:
                q.pop(ref[1])
            return ret
        else:
            return None


def group_clauses(formula):
    cnf = formula.copy()
    temp = []
    i = 0
    while i < len(cnf):
        elm = cnf[i]
        if elm != "and":
            temp.append(elm)
            cnf.pop(i)
        else:
            cnf.insert(i, temp)
            temp = []
            i += 2
    cnf.append(temp)
    return cnf


def print_cnf(cnf, q=None):
    for lit in cnf:
        if q is not None:
            if lit in q:
                print_html(f' <font color="#FF0000"> {lit} </font> ')
            else:
                print_html(f' {lit} ')
        else:
            print_html(f' {lit} ')
    print_html("\n")


def full_cnf_steps(formula):
    new = formula.copy()

    # remove imply and equiv
    q = [formula]
    no_imply = remove_imply(new, q)
    if formula != no_imply:
        print_html(lang.REMOVE_IMPLY, end="\n")
        print_formula(formula, q=q, color=True, cnf=True)
        print_formula(no_imply, q=q, color=True, cnf=True)
        print_html("\n")

    # remove negation before parentheses and remove nand nor nimply xor
    q = [no_imply]
    no_neg = remove_neg(no_imply, q)
    if no_neg != no_imply:
        print_html(lang.REMOVE_NEG, end="\n")
        print_formula(no_imply, q=q, color=True, cnf=True)
        print_formula(no_neg, q=q, color=True, cnf=True)
        print_html("\n")

    # distribute or
    q = [no_neg]
    cnf = distribute(no_neg, q)
    if cnf != no_neg:
        print_html(lang.DISTRIBUTE_OR, end="\n")
        print_formula(no_neg, q=q, color=True, cnf=True)
        print_formula(cnf, q=q, color=True, cnf=True)
        print_html("\n")

    q = []
    simple_cnf = simplify_terms(cnf)
    grouped_cnf = group_clauses(simple_cnf)
    final_cnf = simplify(simple_cnf)
    for clause in grouped_cnf:
        if clause == "and":
            continue
        if clause not in final_cnf:
            q.append(clause)
    if q:
        print_html(lang.SIMPLIFY_CNF, end="\n")
        print_cnf(grouped_cnf, q)
        print_cnf(final_cnf)
        print_html("\n")


def dimacs(cnf: list, variables: list):
    string = f"p cnf {len(variables)} {(len(cnf) + 1) // 2}\n"
    for clause in cnf:
        if clause == "and":
            continue
        n_string = ""
        for i in range(len(clause)):
            elm = clause[i]
            if elm in variables:
                if i == 0:
                    n_string += f"{variables.index(elm) + 1} "
                elif clause[i - 1] == "not":
                    n_string += f"-{variables.index(elm) + 1} "
                else:
                    n_string += f"{variables.index(elm) + 1} "
        string += f"{n_string}0\n"
    return string


def dimacs_to_set(string: str):
    divide = string.split("\n")
    cnf = []
    # num_var=int(divide[0].split(" ")[2])
    num_clauses = int(divide[0].split(" ")[3])
    for i in range(1, num_clauses + 1):
        cls = set()
        clause = divide[i].split(" ")
        for term in clause:
            if term == "0":
                break
            cls.add(int(term))
        cnf.append(cls)
    return cnf


def from_dimacs(string: str):
    divide = string.split("\n")
    cnf = []
    num_var = int(divide[0].split(" ")[2])
    num_clauses = int(divide[0].split(" ")[3])
    for i in range(1, num_clauses + 1):
        cls = []
        clause = divide[i].split(" ")
        for term in clause:
            if term == "0":
                cls.pop()
                break
            if "-" in term:
                cls.append("not")
                cls.append(f"{chr(ord('A') + int(term[1:]) - 1)}")
            else:
                cls.append(f"{chr(ord('A') + int(term) - 1)}")
            cls.append("or")
        cnf.append(cls)
        cnf.append("and")
    cnf.pop()
    list_var = [chr(ord('A') + i) for i in range(num_var)]
    return cnf, list_var


def resolve(cnf):
    global nodes, tree
    new_cnf = cnf.copy()
    units = set([frozenset(clause) for clause in cnf if len(clause) == 1])
    multi = set([frozenset(clause) for clause in cnf if len(clause) > 1])
    multi_unusable = set()
    length = 0
    for i in range(len(cnf)):
        clause = frozenset(cnf[i])
        value = set2str(clause)
        nodes.append(Node(25 + 10 * i + length, 25, value))
        length += get_pixel_length(value.replace("not ", "¬ "), 16, "arial.ttf")
    found_unit = True
    while True:
        if found_unit:
            for unit in units:
                for unit2 in units:
                    if unit == unit2:
                        continue
                    for phi in unit:
                        for psi in unit2:
                            if phi == -1 * psi:
                                add_node(unit, unit2, "{}")
                                print_html(f"<tr><td>{len(new_cnf) + 1}. </td>" + "<td>{}</td>" +
                                           f' <td style="white-space:nowrap">({new_cnf.index(unit) + 1})({new_cnf.index(unit2) + 1})</td><tr>')
                                return True
        found_unit = False
        found = False
        for unit in units:
            for mult in multi:
                if multi in multi_unusable:
                    continue
                for phi in unit:
                    if phi * -1 in mult:
                        found = True
                        new = frozenset([term for term in mult if term != phi * -1])
                        if new in units or new in multi:
                            found = False
                            continue
                        add_node(unit, mult, set2str(new))
                        print_html(f"<tr><td>{len(new_cnf) + 1}. </td>", end="<td>{")
                        print_set(new, table=True)
                        print_html("}</td>")
                        print_html(
                            f' <td style="white-space:nowrap">({new_cnf.index(unit) + 1})({new_cnf.index(mult) + 1})</td></tr>')
                        new_cnf.append(new)
                        if len(new) == 1:
                            found_unit = True
                            units.add(new)
                            break
                        else:
                            multi.add(new)
                            skip = False
                            for lit1 in new:
                                for lit2 in new:
                                    if lit1 == lit2:
                                        continue
                                    if lit1 == -1 * lit2:
                                        multi_unusable.add(new)
                                        skip = True
                                        break
                                if skip:
                                    break
                            break
                if found:
                    break
            if found:
                break
        if found:
            continue
        for A in multi:
            if A in multi_unusable:
                continue
            for B in multi:
                if A == B or B in multi_unusable:
                    continue
                for phi in A:
                    for psi in B:
                        if phi == -1 * psi:
                            found = True
                            new = set([term for term in A if term != phi]).union(
                                set([term for term in B if term != psi]))
                            if new in units or new in multi:
                                found = False
                                continue
                            add_node(A, B, set2str(new))
                            print_html(f"<tr><td>{len(new_cnf) + 1}. </td>", end="<td>{")
                            print_set(new, table=True)
                            print_html("}</td>")
                            print_html(
                                f' <td style="white-space:nowrap">({new_cnf.index(A) + 1})({new_cnf.index(B) + 1})</td></tr>')
                            new_cnf.append(new)
                            if len(new) == 1:
                                found_unit = True
                                units.add(frozenset(new))
                                break
                            else:
                                multi.add(frozenset(new))
                                skip = False
                                for lit1 in new:
                                    for lit2 in new:
                                        if lit1 == lit2:
                                            continue
                                        if lit1 == -1 * lit2:
                                            multi_unusable.add(frozenset(new))
                                            skip = True
                                            break
                                    if skip:
                                        break
                                break
                    if found:
                        break
                if found:
                    break
            if found:
                break
        if found:
            continue
        return False


def resolve_unit(cnf):
    global nodes, tree
    new_cnf = cnf.copy()
    units = set([frozenset(clause) for clause in cnf if len(clause) == 1])
    multi = set([frozenset(clause) for clause in cnf if len(clause) > 1])
    multi_unusable = set()
    length = 0
    for i in range(len(cnf)):
        clause = frozenset(cnf[i])
        value = set2str(clause)
        nodes.append(Node(25 + 10 * i + length, 25, value))
        length += get_pixel_length(value.replace("not ", "¬ "), 16, "arial.ttf")
    found_unit = True
    while True:
        if found_unit:
            for unit in units:
                for unit2 in units:
                    if unit == unit2:
                        continue
                    for phi in unit:
                        for psi in unit2:
                            if phi == -1 * psi:
                                add_node(unit, unit2, "{}")
                                print_html(
                                    f"<tr><td>{len(new_cnf) + 1}. </td>" + "<td>{}</td>" + f' <td style="white-space:nowrap">({new_cnf.index(unit) + 1})({new_cnf.index(unit2) + 1})</td><tr>')
                                return True
        found_unit = False
        found = False
        for unit in units:
            for mult in multi:
                if mult in multi_unusable:
                    continue
                for phi in unit:
                    if phi * -1 in mult:
                        found = True
                        new = frozenset([term for term in mult if term != phi * -1])
                        if new in units or new in multi:
                            found = False
                            continue
                        add_node(unit, mult, set2str(new))
                        print_html(f"<tr><td>{len(new_cnf) + 1}. </td>", end="<td>{")
                        print_set(new, table=True)
                        print_html("}</td>")
                        print_html(
                            f' <td style="white-space:nowrap">({new_cnf.index(unit) + 1})({new_cnf.index(mult) + 1})</td></tr>')
                        new_cnf.append(new)
                        if len(new) == 1:
                            found_unit = True
                            units.add(new)
                            break
                        else:
                            multi.add(new)
                            skip = False
                            for lit1 in new:
                                for lit2 in new:
                                    if lit1 == lit2:
                                        continue
                                    if lit1 == -1 * lit2:
                                        multi_unusable.add(new)
                                        skip = True
                                        break
                                if skip:
                                    break
                            break
                if found:
                    break
            if found:
                break
        if found:
            continue
        return False


def resolve_linear(cnf):
    global nodes, tree
    new_cnf = cnf.copy()
    units = set([frozenset(clause) for clause in cnf if len(clause) == 1])
    multi = set([frozenset(clause) for clause in cnf if len(clause) > 1])
    multi_unusable = set()
    result = None
    length = 0
    for i in range(len(cnf)):
        clause = frozenset(cnf[i])
        value = set2str(clause)
        nodes.append(Node(25 + 10 * i + length, 25, value))
        length += get_pixel_length(value.replace("not ", "¬ "), 16, "arial.ttf")
    found_unit = True
    while True:
        if found_unit and result is None:
            for unit in units:
                for unit2 in units:
                    if unit == unit2:
                        continue
                    for phi in unit:
                        for psi in unit2:
                            if phi == -1 * psi:
                                add_node(unit, unit2, "{}")
                                print_html(
                                    f"<tr><td>{len(new_cnf) + 1}. </td>" + "<td>{}</td>" + f' <td style="white-space:nowrap">({new_cnf.index(unit) + 1})({new_cnf.index(unit2) + 1})</td><tr>')
                                return True
        elif found_unit:
            for unit in units:
                if unit == result:
                    continue
                for phi in unit:
                    for psi in result:
                        if phi == -1 * psi:
                            helper = add_node(result, None, set2str(unit))
                            add_node(result, helper, "{}")
                            print_html(
                                f"<tr><td>{len(new_cnf) + 1}. </td>" + "<td>{}</td>" + f' <td style="white-space:nowrap">({new_cnf.index(unit) + 1})({new_cnf.index(result) + 1})</td><tr>')
                            return True
        found_unit = False
        found = False
        if result is None:
            for unit in units:
                for mult in multi:
                    if mult in multi_unusable:
                        continue
                    for phi in unit:
                        if phi * -1 in mult:
                            found = True
                            new = frozenset([term for term in mult if term != phi * -1])
                            if new in units or new in multi:
                                found = False
                                continue
                            add_node(unit, mult, set2str(new))
                            print_html(f"<tr><td>{len(new_cnf) + 1}. </td>", end="<td>{")
                            print_set(new, table=True)
                            print_html("}</td>")
                            print_html(
                                f' <td style="white-space:nowrap">({new_cnf.index(unit) + 1})({new_cnf.index(mult) + 1})</td></tr>')
                            new_cnf.append(new)
                            if len(new) == 1:
                                found_unit = True
                                units.add(new)
                                result = new
                                break
                            else:
                                multi.add(new)
                                skip = False
                                for lit1 in new:
                                    for lit2 in new:
                                        if lit1 == lit2:
                                            continue
                                        if lit1 == -1 * lit2:
                                            multi_unusable.add(new)
                                            skip = True
                                            break
                                    if skip:
                                        break
                                if not skip:
                                    result = new
                                break
                    if found:
                        break
                if found:
                    break
            if found:
                continue
        if result is None:
            for A in multi:
                if A in multi_unusable:
                    continue
                for B in multi:
                    if A == B or B in multi_unusable:
                        continue
                    for phi in A:
                        for psi in B:
                            if phi == -1 * psi:
                                found = True
                                new = set([term for term in A if term != phi]).union(
                                    set([term for term in B if term != psi]))
                                if new in units or new in multi:
                                    found = False
                                    continue
                                add_node(A, B, set2str(new))
                                print_html(f"<tr><td>{len(new_cnf) + 1}. </td>", end="<td>{")
                                print_set(new, table=True)
                                print_html("}</td>")
                                print_html(
                                    f' <td style="white-space:nowrap">({new_cnf.index(A) + 1})({new_cnf.index(B) + 1})</td></tr>')
                                new_cnf.append(new)
                                if len(new) == 1:
                                    found_unit = True
                                    units.add(frozenset(new))
                                    break
                                else:
                                    multi.add(frozenset(new))
                                    skip = False
                                    for lit1 in new:
                                        for lit2 in new:
                                            if lit1 == lit2:
                                                continue
                                            if lit1 == -1 * lit2:
                                                multi_unusable.add(frozenset(new))
                                                skip = True
                                                break
                                        if skip:
                                            break
                                    break
                        if found:
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                continue
        else:
            for A in multi:
                if A == result or A in multi_unusable:
                    continue
                for phi in A:
                    for psi in result:
                        if phi == -1 * psi:
                            found = True
                            new = set([term for term in A if term != phi]).union(
                                set([term for term in result if term != psi]))
                            if new in units or new in multi:
                                found = False
                                continue
                            helper = add_node(result, None, set2str(A))
                            add_node(result, helper, set2str(new))
                            print_html(f"<tr><td>{len(new_cnf) + 1}. </td>", end="<td>{")
                            print_set(new, table=True)
                            print_html("}</td>")
                            print_html(
                                f' <td style="white-space:nowrap">({new_cnf.index(A) + 1})({new_cnf.index(result) + 1})</td></tr>')
                            new_cnf.append(new)
                            if len(new) == 1:
                                found_unit = True
                                units.add(frozenset(new))
                                result = frozenset(new)
                                break
                            else:
                                multi.add(frozenset(new))
                                skip = False
                                for lit1 in new:
                                    for lit2 in new:
                                        if lit1 == lit2:
                                            continue
                                        if lit1 == -1 * lit2:
                                            multi_unusable.add(frozenset(new))
                                            skip = True
                                            break
                                    if skip:
                                        break
                                if not skip:
                                    result = frozenset(new)
                                break
                    if found:
                        break
                if found:
                    break
            if found:
                continue
        if result is not None:
            result = None
            continue
        return False


def full_cnf(formula):
    form = to_cnf(formula)
    simp = simplify_terms(form)
    cnf = simplify(simp)
    return cnf


def resolution(inp, res_type, reduced):
    global var, output
    tokens = tokenize(inp)
    first_formula = ""
    print_html(lang.INPUT_FORMULA, end=" ")
    for token in tokens:
        first_formula += print_html(token, end=" ")
    if not tokens:
        return print_html(lang.EMPTY_FORMULA)
    formula = add_priority(tokens)
    print_html("\n\n")
    cut = len(output)
    print_html(lang.SIMPLIFIED_FORMULA)
    simple_formula = print_formula(formula) + " "
    if first_formula == simple_formula:
        output = output[:cut]
    else:
        print_html("\n")

    var = find_vars(formula)
    print_html()
    # cnf=full_cnf(formula)

    # dimacs_set=dimacs(cnf,var)
    # print_html(f"DIMACS: \n{dimacs_set}\n")
    bfs = add_priority(tokens)
    print_html(lang.NEGATION_FORMULA, end="\n")
    negate_bfs(bfs)
    negated_formula = negate(formula)
    print_html(lang.NEGATED_FORMULA, end=" ")
    print_formula(negated_formula)
    print_html("\n")
    full_cnf_steps(negated_formula)
    negated_cnf = full_cnf(negated_formula)
    print_html(lang.NEGATED_CNF, end=" ")
    if len(negated_cnf) == 1:
        print_html(*negated_cnf[0], end="")
    else:
        for lit in negated_cnf:
            if len(lit) == 1:
                print_html(lit[0], end=" ")
            elif len(lit) == 2 and lit != "or":
                print_html(*lit, end=" ")
            else:
                print_html(lit, end=" ")
    print_html("\n")
    negated_dimacs = dimacs(negated_cnf, var)
    # print_html(f"Negated DIMACS: \n{negated_dimacs}")
    negated_resolution = dimacs_to_set(negated_dimacs)
    print_html("\n")
    print_html(lang.SET_NOTATION, end="{")
    for s in negated_resolution:
        print_html(end="{")
        print_set(s)
        print_html("}")
    print_html("}\n\n")
    print_html(lang.RES_TABLE)
    print_html("<table>")
    print_html(f'<tr><th>#</th><th>{lang.CLAUSE}</th><th>{lang.CONNECTED}</th></tr>')
    for i in range(len(negated_resolution)):
        s = negated_resolution[i]
        print_html("<tr>")
        print_html(f"<td>{i + 1}. </td>", end="<td>{")
        print_set(s, table=True)
        print_html("}</td><td></td>")
        print_html("</tr>")
    if res_type == "Full":
        result = resolve(negated_resolution)
    elif res_type == "Unit":
        result = resolve_unit(negated_resolution)
    else:
        result = resolve_linear(negated_resolution)
    if not result:
        print_html("</table>")
        print_html(f"{lang.NOT_TAUTOLOGY}\n")
        if reduced:
            print_tree()
        else:
            print_tree("normal")
    else:
        print_html("</table>")
        print_html(f"{lang.TAUTOLOGY}\n")
        if reduced:
            print_tree()
        else:
            print_tree("normal")


@app.route('/', methods=['GET', 'POST'])
def index():
    global output, tree, nodes, lang, latex_tree
    lang = importlib.import_module('langs.slovak')
    output = "<br>"
    tree = ""
    latex_tree = ""
    if request.method == "POST":
        inp = request.form["inp"]
        res_type = request.form["option"]
        try:
            reduced = request.form["reduced"]
            reduced = True
        except Exception:
            reduced = False
        tree = ""
        latex_tree = ""
        nodes = []
        resolution(inp, res_type, reduced)
        output = beautify(output)
        tree = beautify(tree)
        return render_template("index.html", output=output, tree=tree, latex_tree=latex_tree)
    else:
        return render_template("index.html")


@app.route('/indexeng', methods=['GET', 'POST'])
def indexeng():
    global output, tree, nodes, lang, latex_tree
    lang = importlib.import_module('langs.english')
    output = "<br>"
    tree = ""
    latex_tree = ""
    if request.method == "POST":
        inp = request.form["inp"]
        res_type = request.form["option"]
        try:
            reduced = request.form["reduced"]
            reduced = True
        except Exception:
            reduced = False
        tree = ""
        latex_tree = ""
        nodes = []
        resolution(inp, res_type, reduced)
        output = beautify(output)
        tree = beautify(tree)
        return render_template("indexeng.html", output=output, tree=tree, latex_tree=latex_tree)
    else:
        return render_template("indexeng.html")


@app.route("/syntax", methods=['GET'])
def syntax():
    return render_template("syntax.html")


@app.route("/manual", methods=['GET'])
def manual():
    return render_template("manual.html")


@app.route("/truth", methods=['GET'])
def truth():
    return render_template("truth.html")


@app.route("/syntaxen", methods=['GET'])
def syntaxen():
    return render_template("syntaxen.html")


@app.route("/manualen", methods=['GET'])
def manualen():
    return render_template("manualen.html")


@app.route("/truthen", methods=['GET'])
def truthen():
    return render_template("truthen.html")


def print_html(*text, sep=" ", end=""):
    global output
    addition = ""
    for t in text:
        output += str(t)
        addition += str(t)
        if t != text[-1]:
            output += str(sep)
            addition += str(sep)
    output += end
    addition += end
    return addition


def beautify(text: str) -> str:
    text = text.replace("\n", "<br>")
    text = text.replace("( ", "(")
    text = text.replace(" )", ")")
    text = text.replace("[", "(")
    text = text.replace("]", ")")
    text = text.replace("',", " ")
    text = text.replace(",'", " ")
    text = text.replace(", '", " ")
    text = text.replace("'", "")
    text = text.replace(" and ", " ∧ ")
    text = text.replace(" or ", " ∨ ")
    text = text.replace("not ", "¬ ")
    text = text.replace(" imply ", " ⇒ ")
    text = text.replace(" equiv ", " ⇔ ")
    text = text.replace("xor", "⊕")
    text = text.replace("nand", "↑")
    text = text.replace("nor", "↓")
    text = text.replace("nimply", "⇏")
    pattern = r'\b(' + '|'.join(re.escape(name) for name in greek_letters.keys()) + r')\b'
    text = re.sub(pattern, replace_function, text, flags=re.IGNORECASE)
    return text


def replace_function(match):
    key = match.group()
    if key[0].islower():
        return greek_letters[key.lower()]
    else:
        return greek_letters[key.upper()]


def set2str(s):
    if s is None:
        return None
    lists = list(s)
    lists.sort(key=lambda x: abs(x))
    string = "{"
    for elm in lists:
        string += f'{"not " * (elm < 0)}{var[abs(elm) - 1]},'
    return string[:-1] + "}"


def print_set(s, table=False):
    global output
    count = 0
    lists = list(s)
    lists.sort(key=lambda x: abs(x))
    for elm in lists:
        print_html(*f'{"not " * (elm < 0)}{var[abs(elm) - 1]},', sep="", end="")
        count += 1
        if count % 2 == 0 and table:
            print_html("<br>", sep="", end="")
    if count % 2 == 0 and table:
        output = output[:-5]
    else:
        output = output[:-1]


def handle_queue(q, formula):
    if q is not None:
        qu = q.copy()
        if formula in q:
            if type(formula[1]) is list:
                qu.append(formula[1].copy())
            else:
                qu = formula[1]
    else:
        if type(formula[1]) is list:
            qu = formula[1].copy()
        else:
            qu = formula[1]
    return qu


def print_formula(formula, q=None, color=False, cnf=False):
    addition = ""
    if len(formula) == 1:
        if type(formula[0]) is list:
            addition += print_html(*formula[0], end="")
        else:
            addition += print_html(formula[0], end="")
    elif len(formula) == 2:
        qu = handle_queue(q, formula)
        addition += print_html(formula[0], print_recursive(formula[1], formula[0], q=qu, first_iter=True, color=color, cnf=cnf))
    else:
        operator = formula[1]
        red = False
        if q is not None:
            first = False
            for elm in q:
                if formula == elm:
                    if (elm != q[0] or first) and color:
                        operator = ' <font color="#FF0000"> ' + formula[1] + " </font> "
                        red = cnf
                        break
                    if elm == q[0]:
                        first = True
        if red:
            addition += print_html(' <font color="#FF0000"> ' + print_recursive(formula[0], formula[1], q=q, color=color, cnf=cnf), formula[1],
                                   print_recursive(formula[2], formula[1], right=True, q=q, color=color, cnf=cnf) + " </font> ")
        else:
            addition += print_html(print_recursive(formula[0], formula[1], q=q, color=color, cnf=cnf), operator,
                                   print_recursive(formula[2], formula[1], right=True, q=q, color=color, cnf=cnf))
    print_html("\n")
    return addition


def print_recursive(formula, op, right=False, q=None, first_iter=False, color=False, cnf=False):
    if type(formula) is not list:
        return formula
    elif len(formula) == 1:
        return formula[0]
    elif len(formula) == 2:
        qu = handle_queue(q, formula)
        return f"{formula[0]} {print_recursive(formula[1], formula[0], q=qu, color=color, cnf=cnf)}"
    else:
        operat = formula[1]
        start = ""
        end = ""
        if q is not None:
            for elm in q:
                if formula == elm:
                    if (elm != q[0] or first_iter) and color:
                        start = ' <font color="#FF0000"> '
                        end = " </font> "
                        if not cnf:
                            operat = start + formula[1] + end
                            start = ""
                            end = ""
                        break
        if formula[1] == "imply" and op == "imply" and not right:
            return f"{start}({print_recursive(formula[0], formula[1], q=q, color=color, cnf=cnf)} {operat} {print_recursive(formula[2], formula[1], right=True, q=q, color=color, cnf=cnf)}){end}"
        elif formula[1] == "imply" and op == "imply" and right:
            return f"{start}{print_recursive(formula[0], formula[1], q=q, color=color, cnf=cnf)} {operat} {print_recursive(formula[2], formula[1], right=True, q=q, color=color, cnf=cnf)}{end}"
        for operator in operators:
            if formula[1] == operator:
                return f"{start}{print_recursive(formula[0], formula[1], q=q, color=color, cnf=cnf)} {operat} {print_recursive(formula[2], formula[1], right=True, q=q, color=color, cnf=cnf)}{end}"
            elif op == operator:
                return f"{start}({print_recursive(formula[0], formula[1], q=q, color=color, cnf=cnf)} {operat} {print_recursive(formula[2], formula[1], right=True, q=q, color=color, cnf=cnf)}){end}"


class Node:
    def __init__(self, x: int, y: int, value: str):
        self.value = value
        self.x = x
        self.y = y
        self.children = []
        self.parents = []
        self.active = True

    def __eq__(self, other):
        return isinstance(other, Node) and self.x == other.x and self.y == other.y

    def __lt__(self, other):
        if self.y < other.y:
            return True
        if self.y == other.y:
            if self.y > 25:
                if len(self.parents) > len(other.parents):
                    return True
                return False
            if len(self.parents) < len(other.parents):
                return True
            if len(self.parents) == len(other.parents):
                if len(self.children) > 0 and len(other.children) == 0:
                    return True
                if len(self.children) > 0 and len(other.children) > 0:
                    self_min = self.children[0].y
                    other_min = other.children[0].y
                    for child in self.children:
                        if child.y < self_min:
                            self_min = child.y
                    for child in other.children:
                        if child.y < other_min:
                            other_min = child.y
                    return self_min < other_min
        return False

    def intersects(self, other):
        if (self.y == other.y and other.is_active() and
                self.x <= other.x + get_pixel_length(other.value, 16, "arial.ttf") and
                self.x + get_pixel_length(self.value, 16, "arial.ttf") >= other.x):
            return True
        return False

    def is_active(self):
        return self.active

    def deactivate(self):
        self.active = False


def parents(s1, s2):
    node1, node2 = None, None
    if isinstance(s2, Node):
        node2 = s2
    for node in nodes:
        if node.value == set2str(s1):
            node1 = node
            if s2 is None:
                return node1, None
        if node2 is None:
            if node.value == set2str(s2):
                node2 = node
        if node1 is not None and node2 is not None:
            return node1, node2
    return node1, node2


def add_node(s1, s2, val):
    node1, node2 = parents(s1, s2)
    if s2 is None:
        nodes.append(
            Node(node1.x + 25 + get_pixel_length(node1.value.replace("not ", "¬ "), 16, "arial.ttf"), node1.y, val))
        return nodes[-1]
    y = max(node1.y, node2.y) + 40
    for child1 in node1.children:
        for child2 in node2.children:
            if child1 == child2:
                if child1.y > y:
                    y = child1.y
                y += 40
    nodes.append(Node((node1.x + node2.x) // 2, y, val))
    node1.children.append(nodes[-1])
    node2.children.append(nodes[-1])
    nodes[-1].parents.append(node1)
    nodes[-1].parents.append(node2)


def handle_child(node, child):
    global tree, latex_tree
    child.value = child.value.replace("not ", "¬ ")
    tree += f'<line x1="{node.x + get_pixel_length(node.value, 16, "arial.ttf") / 2}" y1="{node.y + 5}" x2="{child.x + get_pixel_length(child.value, 16, "arial.ttf") / 2}" y2="{child.y - 15}" style="stroke:rgb(0,0,0);stroke-width:1" />'
    latex_tree += f'\\draw ({node.x},{-node.y - 10}) -- ({child.x},{-child.y + 10});\n'


def calculate_offset(node):
    global nodes
    offset = 0
    for parent in node.parents:
        offset += parent.x
    if offset != 0:
        offset = offset / len(node.parents)
    node.x = offset
    i = 0
    while i < len(nodes):
        other = nodes[i]
        i += 1
        if other == node and other.value == node.value:
            break
        if node.intersects(other):
            i = 0
            node.x = 25 + other.x + get_pixel_length(other.value, 16, "arial.ttf")
            offset = node.x
    offset += 25 + get_pixel_length(node.value, 16, "arial.ttf")
    return offset


def print_tree(typ="reduced"):
    global tree, output, nodes, latex_tree
    if not nodes:
        return
    x_max = 0
    y_max = nodes[-1].y + 5
    x = 25
    y = 25
    sort = sorted(nodes)
    for i in range(len(sort)):
        if len(sort[i].parents) > 0 or sort[i].y > y:
            break
        offset = 1
        for j in range(i + 1, len(sort)):
            if len(sort[j].parents) > 0 or sort[j].y > y:
                break
            children = recursive_children(sort[i])
            for subchild in children:
                if subchild in sort[j].children:
                    insertion = sort.pop(j)
                    sort.insert(i + offset, insertion)
                    offset += 1
                    break
    nodes = sort
    x_offset = x
    for node in nodes:
        if node.y > y_max:
            y_max = node.y + 5
        node.value = beautify(node.value)
        if node.y > y:
            if not node.parents:
                node.x = x_offset
                continue
            x_offset = calculate_offset(node)
        else:
            node.x = x_offset
            x_offset += 25 + get_pixel_length(node.value, 16, "arial.ttf")
    for node in nodes:
        # if typ=="normal":
        if typ == "reduced":
            if not check_children(node):
                node.deactivate()
                continue
            if node.y == y:
                node.x = x
                x += 25 + get_pixel_length(node.value, 16, "arial.ttf")
            else:
                if not node.parents:
                    node.x = x
                else:
                    x = calculate_offset(node)
        if node.x + get_pixel_length(node.value, 16, "arial.ttf") > x_max:
            x_max = node.x + get_pixel_length(node.value, 16, "arial.ttf")
        tree += f'<text x="{node.x}" y="{node.y}">{node.value}</text>'
        latex_tree += f'\\node at ({node.x},{-node.y}) [] {svg2latex(node.value)};\n'
        for child in node.children:
            if typ == "reduced":
                break
            handle_child(node, child)
    if typ == "reduced":
        for node in nodes:
            if not check_children(node):
                continue
            for child in node.children:
                if not check_children(child):
                    continue
                handle_child(node, child)
    tree += "</svg>"
    latex_tree += "\\end{tikzpicture}"
    tree = f'<br><svg height="{y_max}" width="{x_max + 25}">' + tree
    latex_tree = "\\begin{tikzpicture}[x=0.3mm, y=0.3mm]\n" + latex_tree


def check_children(node):
    if node == nodes[-1]:
        return True
    if not node.children:
        return False
    for child in node.children:
        if check_children(child):
            return True
    return False


def recursive_children(node):
    children = []
    if not node.children:
        return children
    for child in node.children:
        if child == nodes[-1]:
            continue
        children.append(child)
        new_children = recursive_children(child)
        for new_child in new_children:
            children.append(new_child)
    return children


def svg2latex(text):
    if text == "{}":
        return "{$\\square$}"
    out = text.replace("{", "{$\\{")
    out = out.replace("}", "\\}$}")
    for key, operator in operator_dic.items():
        out = out.replace(f" {key} ", f" \\{operator[-1]} ")
        out = out.replace(operator[0], f"\\{operator[-1]}")
    for key, letter in greek_letters.items():
        out = out.replace(letter, f"\\{key}")
    return out


def get_pixel_length(text, font_size, font_name):
    #font = PIL.ImageFont.truetype(font_name, font_size)
    font = PIL.ImageFont.truetype(THIS_FOLDER / f"static/{font_name}", font_size)
    return font.getlength(text)


operator_dic = {}
with open(THIS_FOLDER / "operators.dic", 'r', encoding='utf-8') as f:
    for line in f:
        if line != "":
            arr = line.strip().split(":")
            operator_dic.update({arr[0]: tuple(arr[1].split(", "))})

greek_letters = {}
with open(THIS_FOLDER / "greek.dic", 'r', encoding='utf-8') as f:
    for line in f:
        if line != "":
            arr = line.strip().split(":")
            greek_letters.update({arr[0]: arr[1]})

operators = list(operator_dic.keys())
output = ""
tree = ""
latex_tree = ""
nodes = []
var = []
lang = importlib.import_module('langs.slovak')

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000, debug=True)
