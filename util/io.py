__ORIG_INPUT = input
__ORIG_PRINT = print

__NEWLINE_ACTIVE = False

def newline():
    global __NEWLINE_ACTIVE
    if not __NEWLINE_ACTIVE:
        __ORIG_PRINT('')
    __NEWLINE_ACTIVE = True

def print(*args, **kwargs):
    global __NEWLINE_ACTIVE
    __ORIG_PRINT(*args, **kwargs)
    __NEWLINE_ACTIVE = False

# We always want to go to a new line before and after receiving input
def input(prompt: str) -> str:
    global __NEWLINE_ACTIVE
    newline()
    result = __ORIG_INPUT(prompt)
    __NEWLINE_ACTIVE = False
    newline()
    return result

def yes_or_no(prompt: str) -> bool:
    choice = ''
    while True:
        choice = input(f"{prompt} (y/n): ")
        if choice == 'y' or choice == 'n':
            break
        print('Error: Input must be "y" or "n". Try again.')
    return choice == 'y'
