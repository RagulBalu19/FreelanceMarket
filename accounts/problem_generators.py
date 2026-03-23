import random

def generate_problem():

    a = random.randint(1, 50)
    b = random.randint(1, 50)

    title = "Add Two Numbers"

    description = "Write a program to add two numbers."

    sample_input = f"{a} {b}"

    sample_output = str(a + b)

    testcases = []

    for i in range(5):

        x = random.randint(1, 100)
        y = random.randint(1, 100)

        testcases.append({
            "input": f"{x} {y}",
            "output": str(x + y)
        })

    return {
        "title": title,
        "description": description,
        "sample_input": sample_input,
        "sample_output": sample_output,
        "testcases": testcases
    }