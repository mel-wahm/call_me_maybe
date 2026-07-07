from typing import Any

from llm_sdk import Small_LLM_Model  # type: ignore[attr-defined]
from os import system
from json import load, loads, dumps, dump
from .validation_classes import (
    F_Definition, Fc_Result
)


class FunctionCallingAssistant:

    def __init__(self, f_d: str) -> None:
        self.model = Small_LLM_Model()
        self.encode = self.model.encode
        self.decode = self.model.decode
        self.log = self.model.get_logits_from_input_ids
        self.fd_path = f_d

        with open(self.model.get_path_to_vocab_file(), 'r') as f:
            self.tokens = load(f)

        with open(self.fd_path, 'r') as f:
            o_f = load(f)
            self.functions = [F_Definition(**f) for f in o_f]

        system('clear')

        self.desc = {fn.name: fn.description for fn in self.functions}
        self.function_names = [fn.name for fn in self.functions]

    def get_function_names(self, user_request: str) -> Any:
        formatted_functions = "\n".join(
            f"- {name}: {desc}"
            for name, desc in self.desc.items()
        )
        prompt = f"""<|im_start|>system
Route to one function. List:
{formatted_functions}<|im_end|>
<|im_start|>user
{user_request}<|im_end|>
<|im_start|>assistant
Function name: """
        newly_generated = ""
        e = self.encode(prompt)[0].tolist()
        while True:
            enc = e + (self.encode(newly_generated)[0]).tolist()
            logits = self.log(enc)
            for k, v in self.tokens.items():
                if all(not f.startswith(newly_generated + k)
                       for f in self.function_names):
                    logits[v] = float("-inf")

            for i in range(len(self.tokens), len(logits)):
                logits[i] = float('-inf')

            newly_generated += self.decode(
                [logits.index(max(logits))])
            print('-', end='')
            if newly_generated in self.function_names:
                return newly_generated

    def get_params(self, function_name: str) -> dict[str, Any]:
        for fun in self.functions:
            if fun.name == function_name:
                return ({k: v.type for k, v in fun.parameters.items()})
        return {}

    def build_json(self, user_request: str, function_selected: str) -> str:
        user_request = dumps(user_request)[1:-1]
        j = (f'{{\n"prompt": "{user_request}",\n"name": '
             f'"{function_selected}",\n"parameters": {{')
        return j

    def extract_json(self, user_request: str) -> Any:
        function_selected = self.get_function_names(user_request)
        partial_json = self.build_json(user_request, function_selected)
        prompt = f"""<|im_start|>system
Extract only values explicitly present in the text. Never invent, calculate, or infer missing ones.
<|im_end|>
<|im_start|>user
{user_request}
<|im_end|>
<|im_start|>assistant
{partial_json}"""
        start = len(prompt) - len(partial_json)
        parameters = self.get_params(function_selected)
        new_gen = ""
        for i in range(len(parameters)):
            parameter = list(parameters)[i]
            if parameters[parameter] in ['number', 'integer']:
                new_gen += '"' + parameter + '":'
            else:
                new_gen += '"' + parameter + '": "'
            s = len(new_gen)
            while True:
                print('-', end='', flush=True)
                if parameters[parameter] in ['number', 'integer']:
                    if i != len(parameters) - 1:
                        if '.' in user_request:
                            allowed = '0123456789.,'
                        else:
                            allowed = '0123456789,'
                    else:
                        if '.' in user_request:
                            allowed = '0123456789.}'
                        else:
                            allowed = '0123456789}'
                    enc = self.encode(prompt + new_gen)[0].tolist()
                    logits = self.log(enc)
                    for k, v in self.tokens.items():
                        if k not in allowed and not k == 'Ġ-':
                            logits[v] = float('-inf')
                    for v in range(len(self.tokens), len(logits)):
                        logits[v] = float('-inf')

                    new_gen += self.decode(logits.index(max(logits)))
                    if len(new_gen[s:]) >= 30:
                        if i == len(parameters) - 1:
                            if new_gen.rstrip()[-1] != '}':
                                new_gen += '}'
                        else:
                            new_gen += ','
                        break
                    if new_gen[-1] in ',}':
                        break
                else:
                    enc = self.encode(prompt + new_gen)[0].tolist()
                    logits = self.log(enc)
                    for k, v in self.tokens.items():
                        if i == len(parameters) - 1 and ',' in k:
                            logits[v] = float('-inf')
                        if i != len(parameters) - 1 and '}' in k:
                            logits[v] = float('-inf')
                        if any(ord(c) < 32 for c in k) or k == 'Ċ':
                            logits[v] = float('-inf')
                    for v in range(len(self.tokens), len(logits)):
                        logits[v] = float('-inf')

                    to_append = self.decode(logits.index(max(logits)))

                    if '"' in to_append and i == len(parameters) - 1:
                        new_gen += to_append.split('"')[0] + '"'
                    elif '"' in to_append:
                        new_gen += to_append.split('"')[0] + '", '
                    else:
                        new_gen += to_append
                    if '"' in new_gen[s:]:
                        if i == len(parameters) - 1:
                            new_gen += to_append.split('"')[0] +  '}'
                        elif i != len(parameters) - 1\
                                and ',' not in new_gen[s:]:
                            new_gen += to_append.split('"')[0] +  ','
                        break

                    if len(new_gen[s:]) >= 80:
                        if i == len(parameters) - 1:
                            new_gen += to_append.split('"')[0] + '"}'
                        else:
                            new_gen += to_append.split('"')[0] + '",'
                        break
                # print(new_gen, flush=True)

        raw_json_string = (prompt + new_gen)[start:] + '\n}'
        data_dict = loads(raw_json_string)
        validated = Fc_Result(**data_dict)
        print('\r')
        print(f"{validated.model_dump_json(indent=4)}", end='\n\n')
        return validated.model_dump_json(indent=4)


class TestRunner:

    def __init__(self, assistant: FunctionCallingAssistant,
                 tests_path: str,
                 o_path: str):
        self.assistant = assistant
        self.test = tests_path
        self.output = o_path

        with open(self.test) as f:
            self.tests = load(f)

    def run(self) -> None:
        all_results = []
        for test in self.tests:
            res_str = self.assistant.extract_json(test['prompt'])

            result_dict = loads(res_str)
            all_results.append(result_dict)

        # with open(self.output, 'w') as f:
        #     dump(all_results, f, indent=4)
