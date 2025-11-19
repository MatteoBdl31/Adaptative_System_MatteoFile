# -*- coding: utf-8 -*-

from backend.db import get_rules

def evaluate_condition(condition, user, context):
    clauses = condition.split("AND")
    for clause in clauses:
        clause = clause.strip()
        if "=" in clause and "CONTAINS" not in clause:
            key, val = clause.split("=")
            key, val = key.strip(), val.strip()
            if key.startswith("performance."):
                perf_key = key.split(".")[1]
                if user.get("performance", {}).get(perf_key, 0) < float(val):
                    return False
            elif key in user and str(user[key]) != val:
                return False
            elif key in context and str(context[key]) != val:
                return False
        elif "<=" in clause:
            key, val = clause.split("<=")
            if int(context.get(key.strip(), 9999)) > int(val.strip()):
                return False
        elif ">=" in clause:
            key, val = clause.split(">=")
            if int(user.get(key.strip(), 0)) < int(val.strip()):
                return False
        elif "CONTAINS" in clause:
            key, val = clause.split("CONTAINS")
            if val.strip() not in user.get(key.strip(), []):
                return False
    return True

def apply_adaptation(quiz, adaptation):
    extra = {}
    for rule in adaptation.split(";"):
        key, val = rule.split("=")
        key, val = key.strip(), val.strip()
        if key == "timer":
            quiz[key] = val.lower() == "true"
        elif key == "questions":
            quiz[key] = int(val)
        elif key == "allowed_quizzes":
            extra["allowed_quizzes"] = [f.strip() for f in val.split(",")]
        else:
            quiz[key] = val
    return quiz, extra

def adapt_quiz(user, context):
    quiz = {"difficulty": "medium", "questions": 10, "timer": False, "display": "classic"}
    allowed_quizzes = []
    rules = get_rules()
    for rule in rules:
        if evaluate_condition(rule["condition"], user, context):
            quiz, extra = apply_adaptation(quiz, rule["adaptation"])
            if "allowed_quizzes" in extra:
                allowed_quizzes = extra["allowed_quizzes"]
    return quiz, allowed_quizzes
