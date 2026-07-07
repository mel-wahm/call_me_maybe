from .constraining import (
    FunctionCallingAssistant, TestRunner
)
import argparse
from json import JSONDecodeError
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--functions_definition',
                        default='data/input/function_definition.json',
                        help='Path to the functions definition file')
    parser.add_argument('--input',
                        default='data/input/function_calling_tests.json',
                        help='Path to the input tests file')
    parser.add_argument('--output',
                        default='data/output/function_calling_results.json',
                        help='Path to the output results file')
    args = parser.parse_args()
    f_path = args.functions_definition
    t_path = args.input
    o_path = args.output
    assistant = FunctionCallingAssistant(f_path)
    runner = TestRunner(assistant, t_path, o_path)
    runner.run()


if __name__ == '__main__':
    try:
        main()
    except FileNotFoundError as e:
        print(f'Error: File not found: {e}')
        sys.exit(1)
    except JSONDecodeError as e:
        print(f'Error: Invalid JSON: {e}')
        sys.exit(1)
    except KeyboardInterrupt:
        print('\nInterrupted by user')
        sys.exit(0)
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)
