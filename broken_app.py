# broken_app.py
# Intentional bug for testing the Self-Healing Python Code Agent.

def calculate_salary(employee):
    # BUG: "bonus" does not exist in the dictionary.
    # Fixed by using .get("bonus", 0) to avoid KeyError when "bonus" is missing.
    total_salary = employee["salary"] + employee.get("bonus", 0)
    return total_salary


def main():
    employee = {
        "name": "Alex",
        "salary": 50000
    }

    total = calculate_salary(employee)
    print(f"{employee['name']}'s total salary: {total}")


if __name__ == "__main__":
    main()