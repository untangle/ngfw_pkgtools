# Project Overview
ngfw_pkgtools is an assortment of scripts used to add to the quality of life of working with several products. These include NGFW, MFW, EFW, Velo, and WAF.

## Key files and concepts
- aws/ - AWS specific scripts and data
- lib/ - shared libraries for common data points
- tests/ - test related paths
- compare-branches.py - script leveraged by products for comparing and merging release branches into the 'master' or 'main' branches
- create-branch.py - script leveraged by products for branch creation process

## Ground Rules/Standards

Methods should be 60 lines or less

Never process JSON / XML by hand (i.e. string building / parsing) - avoid string parsing in general as much as possible (every string replace is O(n)!)

Never have an empty catch or exception handling statement (at least provide a comment why it is empty)

Never add handling for conditions that are not logically expected (aka "just-in-case" coding)

When creating a class, make sure it fits into a class hierarchy / relational diagram. If it does not, re-think the purpose of the class, or escalate re-design of the class hierarchy

Choose commonly re-usable pattern over less commonly re-usable pattern

Avoid methods that are only one line (few exception are pass-through classes, data structure / architecture obfuscations, etc)

Do not leave commented out code in the code base - that is what Source Control is for. If you think some code may be useful in the future, remove it and add a comment that additional logic is available via version history.

Default value for a string should be NULL not empty string.

Avoid exception-driven programming. Throwing exceptions is costly. Catching and re-throwing doubles that cost. If you are relying on throwing custom exceptions to communicate errors, you likely have flaws on your design.

SQL queries must be parametrized - NEVER pass non-constant values directly into a SQL query, NEVER attempt to escape parameters manually

FIX any query you come across that does not use parameters
		
Method parameters should be passed in separately rather than passing in a single object that contains all of the parameters.  This makes the code more readable because you do not need to look up the object definition to know what parameters are required.

Do NOT have methods that can return different types, even though this is allowed in e.g. PHP and Python. If you are doing this, your design needs work/improvements.

Code documentation is required! Self-documenting code may exist in the universe, however, the complaint that the code is "documented too well" does not. 

Comment code you add, especially public methods. More commentary is generally better for public methods.

Add new unit tests for new functionality, or new test cases for new cases that arise.

Deduplicate code when necessary. If something is repeated twice with different variables, go back and unify the code.

When finishing a task, run make format, then make lint and fix all lingering linter issues. If the make commands do not exist, we should add them. The standard formatters and linters we use are:
- Golang: go vet, gofmt
- Python: ruff 
- C/C++: clang-format
- bash: shellcheck shfmt 


## Architectural Notes
N/A

## Wrapup Checklist
The 'wrapup checklist' is a list of things to do as we finish a ticket:
1. Run make test and fix all errors in unit tests.

2. Run make format then make lint and fix all linter issues.

3. Run git fetch origin and then git diff origin/master and examine the output -- check that we followed the basic ground rules, that the code we added makes sense and look for duplication or bugs.

## Common Commands
N/A


## Notes
N/A


