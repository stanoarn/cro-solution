---
version: 0.1.0
---

# Zadání

Přečtěte si prosím zadání zapsané v dokumentu [assignment-cs](./assignment-cs.md).

## Požadavky

- K řešení přiložte instrukce jak ho sestavit a spustit. Vše ideálně zapsané ve vašem vlastním dokumentu `README.md`.
- Pokud je řešení v jazyce Python, zkuste vytvořit instalovatelný balík pomocí `setup.py` nebo `pyproject.toml`. 
- Pokud je řešení v jiném jazyce, použijte standardní řešení pro daný jazyk, abychom ho uměli sestavit a spustit.
- Svoje řešení nasdílejte jako odkaz na svůj GitHub repozitář nebo pošlete jako ZIP.
- Pokud je v zadání chyba nebo nejasnost, neváhejte se ozvat.

## Doporučení

Pro řešení v jazyce Python je ideální, pokud vytvoříte balík a zároveň definujete konzolový program.
Postačí opravdu jen několik řádek. Pokud je struktura vašeho projektu např.:

```shell
solution/
  setup.py
  solution.py
```
, kde `solution.py` obsahuje funkci `main()`, potom stačí definovat `setup.py` následovně.

```python
from setuptools import setup

PROGRAM_NAME = "program"

setup(
    name=PROGRAM_NAME,
    version="1.0.0",
    py_modules=[solution],
    entry_points={
        "console_scripts": [
            f"{PROGRAM_NAME}=solution:main",
        ],
    },
    install_requires=['tqdm']
)
```

Potom je jednoduché instalovat vaše řešení a zavolat program z příkazové řádky.

```powershell
py -3.11 -m venv --upgrade-deps .venv
.\.venv\Scripts\activate
pip install --editable .
...
Successfully installed solution-1.0.0
```

```powershell
solution --version
solution 0.3.0
```

Přepínač `-e` nebo `--edtable` vám pomůže při vývoji, protože vytváří jen symbolikcý odkaz a všechny změny ve zdrojovém kódu se okamžitě projeví i bez opětovné instalace balíku.

- Pro automatické formátování a řazení importů využijte nástroj [black](https://black.readthedocs.io/en/stable/) respektive [isort](https://pycqa.github.io/isort/).
- Pokud využíváte [ViSual Studio Code](https://code.visualstudio.com/), pak se hodí [rozšíření pro Python](https://code.visualstudio.com/docs/languages/python).
- Pro kontrolu typů můžete využít balík a nástroje [mypy](https://mypy-lang.org/) nebo Pyright např. skrze rozšření [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance). 
